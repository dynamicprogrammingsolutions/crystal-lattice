import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import {
  appendSpan,
  loadSpans,
  removeFirstSpans,
  type SpanCacheStore,
} from './spanCache';
import type { HumanTimeSpan } from './spanTracker';

export const HUMAN_TIME_ACTION_ID = 'record_human_time_spans';
export const HUMAN_TIME_ACTION_OWNER = 'application';
export const DEFAULT_HUMAN_TIME_PLUGIN_ID = 'duration_tracking_app';

export const DEFAULT_UPLOAD_BATCH_LIMIT = 100;
export const DEFAULT_MAX_SPAN_AGE_MS = 5 * 60 * 1000;
export const DEFAULT_AGE_CHECK_INTERVAL_MS = 60 * 1000;
export const DEFAULT_CLOSE_DEBOUNCE_MS = 2_000;
export const DEFAULT_BUSY_RETRY_INTERVAL_MS = 15 * 1000;

export type FlushOutcome =
  | 'disabled'
  | 'no-connection'
  | 'busy'
  | 'empty'
  | 'flushed'
  | 'transient-failure'
  | 'definitive-failure';

/**
 * Classify an upload failure: HTTP 404 (unknown plugin or action) and 400
 * (invalid action inputs) are definitive — retrying cannot fix them and the
 * app warns the user once. Network errors, timeouts, and server errors are
 * transient and retry silently on the next trigger.
 */
export function isDefinitiveActionFailure(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error ?? '');
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
  'unknown_action',
  'unknown_plugin',
  'ambiguous_action',
  'validation',
  'not_found',
]);

export function isDefinitiveActionErrorType(errorType: unknown): boolean {
  return (
    typeof errorType === 'string' && DEFINITIVE_ACTION_ERROR_TYPES.has(errorType)
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

export interface HumanTimeUploaderOptions {
  getBackend: () => AgentBackend | null;
  getConnectionId: () => string | null;
  getPluginId: () => string;
  isEnabled: () => boolean;
  isBusy: () => boolean;
  /** Called at most once per arm cycle on a definitive upload failure. */
  onDefinitiveFailure?: (error: unknown) => void;
  batchLimit?: number;
  maxSpanAgeMs?: number;
  ageCheckIntervalMs?: number;
  closeDebounceMs?: number;
  busyRetryIntervalMs?: number;
  store?: SpanCacheStore;
  now?: () => number;
}

/**
 * Drains the durable span cache in batches through the ingestion action.
 * Triggers: span closes (debounced), the periodic age check, and explicit
 * flush calls (connection open, app foreground). Busy connections defer;
 * failures retain every span for the next trigger.
 */
export class HumanTimeSpanUploader {
  private readonly options: HumanTimeUploaderOptions;
  private readonly batchLimit: number;
  private readonly maxSpanAgeMs: number;
  private readonly ageCheckIntervalMs: number;
  private readonly closeDebounceMs: number;
  private readonly busyRetryIntervalMs: number;
  private readonly now: () => number;
  private flushing = false;
  private closeDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  private ageCheckTimer: ReturnType<typeof setInterval> | null = null;
  private busyRetryTimer: ReturnType<typeof setInterval> | null = null;
  private definitiveFailureReported = false;

  constructor(options: HumanTimeUploaderOptions) {
    this.options = options;
    this.batchLimit = options.batchLimit ?? DEFAULT_UPLOAD_BATCH_LIMIT;
    this.maxSpanAgeMs = options.maxSpanAgeMs ?? DEFAULT_MAX_SPAN_AGE_MS;
    this.ageCheckIntervalMs =
      options.ageCheckIntervalMs ?? DEFAULT_AGE_CHECK_INTERVAL_MS;
    this.closeDebounceMs = options.closeDebounceMs ?? DEFAULT_CLOSE_DEBOUNCE_MS;
    this.busyRetryIntervalMs =
      options.busyRetryIntervalMs ?? DEFAULT_BUSY_RETRY_INTERVAL_MS;
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

  /** Begin the periodic max-age check. */
  start(): void {
    if (this.ageCheckTimer !== null) return;
    this.ageCheckTimer = setInterval(() => {
      void this.checkAge();
    }, this.ageCheckIntervalMs);
  }

  /**
   * A connection became usable: flush now, and while the app reports busy
   * keep retrying until in-flight work settles (first open defers).
   */
  notifyConnectionUsable(): void {
    void this.flush().then((outcome) => {
      if (outcome === 'busy') {
        this.scheduleBusyRetry();
      }
    });
  }

  private scheduleBusyRetry(): void {
    if (this.busyRetryTimer !== null) return;
    this.busyRetryTimer = setInterval(() => {
      void this.flush().then((outcome) => {
        if (outcome !== 'busy') {
          this.clearBusyRetry();
        }
      });
    }, this.busyRetryIntervalMs);
  }

  private clearBusyRetry(): void {
    if (this.busyRetryTimer !== null) {
      clearInterval(this.busyRetryTimer);
      this.busyRetryTimer = null;
    }
  }

  dispose(): void {
    if (this.closeDebounceTimer !== null) {
      clearTimeout(this.closeDebounceTimer);
      this.closeDebounceTimer = null;
    }
    if (this.ageCheckTimer !== null) {
      clearInterval(this.ageCheckTimer);
      this.ageCheckTimer = null;
    }
    this.clearBusyRetry();
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

  private async checkAge(): Promise<void> {
    const connectionId = this.options.getConnectionId();
    if (!connectionId) return;
    const pending = await loadSpans(connectionId, this.options.store);
    const oldest = pending[0];
    if (!oldest) return;
    const oldestMs = Date.parse(oldest.from);
    if (!Number.isFinite(oldestMs)) return;
    if (this.now() - oldestMs >= this.maxSpanAgeMs) {
      await this.flush();
    }
  }

  async flush(): Promise<FlushOutcome> {
    if (this.flushing) return 'busy';
    if (!this.options.isEnabled()) return 'disabled';
    const backend = this.options.getBackend();
    const connectionId = this.options.getConnectionId();
    if (!backend || !connectionId) return 'no-connection';
    if (this.options.isBusy()) return 'busy';

    this.flushing = true;
    try {
      let flushedAny = false;
      for (;;) {
        const pending = await loadSpans(connectionId, this.options.store);
        if (pending.length === 0) {
          return flushedAny ? 'flushed' : 'empty';
        }
        const batch = pending.slice(0, this.batchLimit);
        // The ingestion contract is snake_case (`session_id`); the app's
        // internal span type is camelCase. Convert at the boundary.
        const wireSpans = batch.map((span) => ({
          session_id: span.sessionId,
          from: span.from,
          to: span.to,
        }));
        try {
          const response = await backend.executeAction({
            pluginId: this.options.getPluginId(),
            actionId: HUMAN_TIME_ACTION_ID,
            actionOwner: HUMAN_TIME_ACTION_OWNER,
            inputs: {
              request_id: batchRequestId(wireSpans),
              spans: wireSpans,
            },
          });
          // The action protocol reports failures as a structured error
          // response (HTTP 200, status "error"), not as an HTTP error.
          if (!response || response.status !== 'ok') {
            const errorType = (response as { error_type?: unknown } | null)
              ?.error_type;
            const message =
              (response as { message?: unknown } | null)?.message ??
              'action failed';
            const error = new Error(
              `${String(message)} (error_type: ${String(errorType ?? 'unknown')})`,
            );
            if (isDefinitiveActionErrorType(errorType)) {
              this.reportDefinitiveFailure(error);
              return 'definitive-failure';
            }
            return 'transient-failure';
          }
        } catch (error) {
          if (isDefinitiveActionFailure(error)) {
            this.reportDefinitiveFailure(error);
            return 'definitive-failure';
          }
          return 'transient-failure';
        }
        // Confirmed: remove exactly the spans this batch uploaded. Appends
        // only ever push to the end, so the first N are this batch.
        await removeFirstSpans(connectionId, batch.length, this.options.store);
        flushedAny = true;
      }
    } finally {
      this.flushing = false;
    }
  }
}

export type { HumanTimeSpan };
export { appendSpan };