import type { AgentBackend } from "@crystal-lattice/frontend-sdk";

import {
  appendSpan,
  loadSpans,
  removeSpans,
  type SpanCacheStore,
} from "./spanCache";
import type { HumanTimeSpan } from "./spanTracker";

export const HUMAN_TIME_ACTION_ID = "record_human_time_spans";
export const HUMAN_TIME_ACTION_OWNER = "application";
export const DEFAULT_HUMAN_TIME_PLUGIN_ID = "duration_tracking_app";

export const DEFAULT_UPLOAD_BATCH_LIMIT = 100;
export const DEFAULT_CLOSE_DEBOUNCE_MS = 2_000;
export const DEFAULT_TRANSIENT_RETRY_INTERVAL_MS = 30 * 1000;

export type FlushOutcome =
  | "disabled"
  | "no-connection"
  | "in-progress"
  | "empty"
  | "flushed"
  | "partial-failure"
  | "transient-failure"
  | "definitive-failure";

export interface HumanTimeIngestionResult {
  recorded: number;
  merged: number;
  skipped: number;
  absorbed: number;
  duplicate: boolean;
}

export interface HumanTimeUploadEvent {
  outcome:
    | "uploading"
    | "flushed"
    | "partial-failure"
    | "transient-failure"
    | "definitive-failure";
  attemptedAt: string;
  requestId: string;
  batchSize: number;
  spans: HumanTimeSpan[];
  result: HumanTimeIngestionResult | null;
  error: string | null;
}

interface BatchAttempt {
  outcome: "flushed" | "skipped" | "transient-failure" | "definitive-failure";
  result: HumanTimeIngestionResult | null;
}

/**
 * Classify an upload failure: HTTP 404 (unknown plugin or action) and 400
 * (invalid action inputs) are definitive — retrying cannot fix them and the
 * app warns the user once. Network errors, timeouts, and server errors are
 * transient and retry silently on the next trigger.
 */
export function isDefinitiveActionFailure(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const match = /^HTTP (\d{3})\b/.exec(message);
  if (!match) return false;
  const status = Number(match[1]);
  return status === 404 || status === 400;
}

/**
 * Action-level error types that retrying cannot fix. The backend reports
 * these as a structured error response (HTTP 200, status "error") rather
 * than an HTTP error, so the uploader must classify them from the body.
 */
const DEFINITIVE_ACTION_ERROR_TYPES = new Set([
  "unknown_action",
  "unknown_plugin",
  "ambiguous_action",
  "validation",
  "not_found",
]);

export function isDefinitiveActionErrorType(errorType: unknown): boolean {
  return (
    typeof errorType === "string" &&
    DEFINITIVE_ACTION_ERROR_TYPES.has(errorType)
  );
}

/**
 * Deterministic, content-derived request id: the same batch keeps the same
 * id across retries (the backend's request-id dedup makes retries
 * idempotent), and a new batch gets a fresh id.
 */
function batchRequestId(spans: Array<{ session_id: string | null }>): string {
  const payload = JSON.stringify(spans);
  let first = 0x811c9dc5;
  let second = 0x01935713;
  for (let index = 0; index < payload.length; index += 1) {
    const code = payload.charCodeAt(index);
    // FNV-1a style mixing over the serialized batch.
    first = Math.imul(first ^ code, 0x01000193) >>> 0;
    second = Math.imul(second + code + index, 0x85ebca6b) >>> 0;
  }
  return `human-time-${first.toString(16)}-${second.toString(16)}`;
}

function spanIdentity(span: HumanTimeSpan): string {
  return `${span.sessionId ?? ""}\u0000${span.from}\u0000${span.to}`;
}

export interface HumanTimeUploaderOptions {
  getBackend: () => AgentBackend | null;
  getConnectionId: () => string | null;
  getPluginId: () => string;
  isEnabled: () => boolean;
  /** Called at most once per arm cycle on a definitive upload failure. */
  onDefinitiveFailure?: (error: unknown) => void;
  onUploadEvent?: (event: HumanTimeUploadEvent) => void;
  batchLimit?: number;
  closeDebounceMs?: number;
  transientRetryIntervalMs?: number;
  store: SpanCacheStore;
  now?: () => number;
}

/**
 * Drains the durable span cache in batches through the ingestion action.
 * Triggers: span closes (debounced), connection open, app foreground, and
 * explicit flush. Transient failures retry on one fixed timer; all failures
 * retain every unconfirmed span.
 */
export class HumanTimeSpanUploader {
  private readonly options: HumanTimeUploaderOptions;
  private readonly batchLimit: number;
  private readonly closeDebounceMs: number;
  private readonly transientRetryIntervalMs: number;
  private readonly now: () => number;
  private flushing = false;
  private closeDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  private transientRetryTimer: ReturnType<typeof setTimeout> | null = null;
  private definitiveFailureReported = false;

  constructor(options: HumanTimeUploaderOptions) {
    this.options = options;
    this.batchLimit = options.batchLimit ?? DEFAULT_UPLOAD_BATCH_LIMIT;
    this.closeDebounceMs = options.closeDebounceMs ?? DEFAULT_CLOSE_DEBOUNCE_MS;
    this.transientRetryIntervalMs =
      options.transientRetryIntervalMs ?? DEFAULT_TRANSIENT_RETRY_INTERVAL_MS;
    this.now = options.now ?? (() => Date.now());
  }

  /** Schedule the debounced flush that follows a span close. */
  notifySpanClosed(): void {
    if (this.closeDebounceTimer !== null) {
      clearTimeout(this.closeDebounceTimer);
    }
    this.closeDebounceTimer = setTimeout(() => {
      this.closeDebounceTimer = null;
      void this.flush();
    }, this.closeDebounceMs);
  }

  /** A connection became usable; drain any durable pending spans now. */
  notifyConnectionUsable(): void {
    void this.flush();
  }

  /** The app returned to the foreground; drain durable pending spans now. */
  notifyAppForeground(): void {
    void this.flush();
  }

  private scheduleTransientRetry(): void {
    if (this.transientRetryTimer !== null) return;
    this.transientRetryTimer = setTimeout(() => {
      this.transientRetryTimer = null;
      void this.flush();
    }, this.transientRetryIntervalMs);
  }

  private clearTransientRetry(): void {
    if (this.transientRetryTimer !== null) {
      clearTimeout(this.transientRetryTimer);
      this.transientRetryTimer = null;
    }
  }

  dispose(): void {
    if (this.closeDebounceTimer !== null) {
      clearTimeout(this.closeDebounceTimer);
      this.closeDebounceTimer = null;
    }
    this.clearTransientRetry();
  }

  /** Re-arm the one-time definitive-failure warning (setting changed). */
  rearmWarning(): void {
    this.definitiveFailureReported = false;
  }

  private reportDefinitiveFailure(error: unknown): void {
    if (this.definitiveFailureReported) return;
    if (!this.options.onDefinitiveFailure) return;
    this.definitiveFailureReported = true;
    try {
      this.options.onDefinitiveFailure(error);
    } catch {
      // Telemetry must never break the caller.
    }
  }

  private reportUploadEvent(event: HumanTimeUploadEvent): void {
    try {
      this.options.onUploadEvent?.(event);
    } catch {
      // Diagnostics must never break telemetry.
    }
  }

  private async attemptBatch(
    backend: AgentBackend,
    connectionId: string,
    batch: HumanTimeSpan[],
  ): Promise<BatchAttempt> {
    const wireSpans = batch.map((span) => ({
      session_id: span.sessionId,
      from: span.from,
      to: span.to,
    }));
    const requestId = batchRequestId(wireSpans);
    const attemptedAt = new Date(this.now()).toISOString();
    this.reportUploadEvent({
      outcome: "uploading",
      attemptedAt,
      requestId,
      batchSize: batch.length,
      spans: batch,
      result: null,
      error: null,
    });
    try {
      const response = await backend.executeAction({
        pluginId: this.options.getPluginId(),
        actionId: HUMAN_TIME_ACTION_ID,
        actionOwner: HUMAN_TIME_ACTION_OWNER,
        inputs: {
          request_id: requestId,
          spans: wireSpans,
        },
      });
      if (!response || response.status !== "ok") {
        const errorType = (response as { error_type?: unknown } | null)
          ?.error_type;
        const message =
          (response as { message?: unknown } | null)?.message ??
          "action failed";
        const error = new Error(
          `${String(message)} (error_type: ${String(errorType ?? "unknown")})`,
        );
        if (isDefinitiveActionErrorType(errorType)) {
          this.reportDefinitiveFailure(error);
          this.reportUploadEvent({
            outcome: "definitive-failure",
            attemptedAt,
            requestId,
            batchSize: batch.length,
            spans: batch,
            result: null,
            error: error.message,
          });
          return { outcome: "definitive-failure", result: null };
        }
        this.reportUploadEvent({
          outcome: "transient-failure",
          attemptedAt,
          requestId,
          batchSize: batch.length,
          spans: batch,
          result: null,
          error: error.message,
        });
        this.scheduleTransientRetry();
        return { outcome: "transient-failure", result: null };
      }
      const rawResult =
        response.result && typeof response.result === "object"
          ? response.result
          : {};
      const result: HumanTimeIngestionResult = {
        recorded: Number(rawResult.recorded ?? 0),
        merged: Number(rawResult.merged ?? 0),
        skipped: Number(rawResult.skipped ?? 0),
        absorbed: Number(rawResult.absorbed ?? 0),
        duplicate: rawResult.duplicate === true,
      };
      if (result.skipped > 0) {
        const error = `The telemetry plugin skipped ${result.skipped} span${
          result.skipped === 1 ? "" : "s"
        }.`;
        this.reportUploadEvent({
          outcome: "partial-failure",
          attemptedAt,
          requestId,
          batchSize: batch.length,
          spans: batch,
          result,
          error,
        });
        return { outcome: "skipped", result };
      }
      await removeSpans(connectionId, batch, this.options.store);
      this.clearTransientRetry();
      this.reportUploadEvent({
        outcome: "flushed",
        attemptedAt,
        requestId,
        batchSize: batch.length,
        spans: batch,
        result,
        error: null,
      });
      return { outcome: "flushed", result };
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : String(error ?? "Upload failed");
      if (isDefinitiveActionFailure(error)) {
        this.reportDefinitiveFailure(error);
        this.reportUploadEvent({
          outcome: "definitive-failure",
          attemptedAt,
          requestId,
          batchSize: batch.length,
          spans: batch,
          result: null,
          error: message,
        });
        return { outcome: "definitive-failure", result: null };
      }
      this.reportUploadEvent({
        outcome: "transient-failure",
        attemptedAt,
        requestId,
        batchSize: batch.length,
        spans: batch,
        result: null,
        error: message,
      });
      this.scheduleTransientRetry();
      return { outcome: "transient-failure", result: null };
    }
  }

  async flush(): Promise<FlushOutcome> {
    if (this.flushing) return "in-progress";
    if (!this.options.isEnabled()) return "disabled";
    const backend = this.options.getBackend();
    const connectionId = this.options.getConnectionId();
    if (!backend || !connectionId) return "no-connection";

    this.flushing = true;
    try {
      let flushedAny = false;
      const rejected = new Map<string, HumanTimeSpan>();
      for (;;) {
        const pending = await loadSpans(connectionId, this.options.store);
        const eligible = pending.filter(
          (span) => !rejected.has(spanIdentity(span)),
        );
        if (eligible.length === 0) {
          if (rejected.size === 0) {
            return flushedAny ? "flushed" : "empty";
          }
          const rejectedSpans = pending.filter((span) =>
            rejected.has(spanIdentity(span)),
          );
          const rejectedCount = rejectedSpans.length;
          this.reportUploadEvent({
            outcome: "partial-failure",
            attemptedAt: new Date(this.now()).toISOString(),
            requestId: "human-time-partial",
            batchSize: rejectedCount,
            spans: rejectedSpans,
            result: {
              recorded: 0,
              merged: 0,
              skipped: rejectedCount,
              absorbed: 0,
              duplicate: false,
            },
            error: flushedAny
              ? `${rejectedCount} span${
                  rejectedCount === 1 ? "" : "s"
                } could not be accepted; other spans were uploaded.`
              : `${rejectedCount} span${
                  rejectedCount === 1 ? "" : "s"
                } could not be accepted and remain pending.`,
          });
          return "partial-failure";
        }

        const batch = eligible.slice(0, this.batchLimit);
        const attempt = await this.attemptBatch(backend, connectionId, batch);
        if (attempt.outcome === "flushed") {
          flushedAny = true;
          continue;
        }
        if (attempt.outcome === "transient-failure") {
          return "transient-failure";
        }
        if (attempt.outcome === "definitive-failure") {
          return "definitive-failure";
        }

        if (batch.length === 1) {
          rejected.set(spanIdentity(batch[0]), batch[0]);
          continue;
        }

        for (const span of batch) {
          const isolated = await this.attemptBatch(backend, connectionId, [
            span,
          ]);
          if (isolated.outcome === "flushed") {
            flushedAny = true;
            continue;
          }
          if (isolated.outcome === "skipped") {
            rejected.set(spanIdentity(span), span);
            continue;
          }
          return isolated.outcome;
        }
      }
    } finally {
      this.flushing = false;
    }
  }
}

export type { HumanTimeSpan };
export { appendSpan };
