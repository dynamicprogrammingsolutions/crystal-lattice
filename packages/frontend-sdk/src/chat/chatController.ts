import type { AgentBackend } from '../backend/backend';
import type { Event } from '../types/events';
import type { IndexedMessage } from '../types/messages';
import { parseIndexRangeText } from '../utils/range';
import { PollingEventSource, type PollingStatus } from '../events/pollingEventSource';
import { SimpleSubscribable } from '../util/subscribable';
import { reduceMessageHistoryWithOptions } from './messageHistoryReducer';
import {
  reduceStreamingState,
  type RequestErrorState,
  type StreamingRow,
} from './streamingStateReducer';

export type { StreamingRow, RequestErrorState } from './streamingStateReducer';

export interface ChatControllerState {
  sessionId: string;
  loading: boolean;
  messages: IndexedMessage[];
  /**
   * The last range used for `/messages` loads.
   *
   * Indices follow the server semantics (Python slice-like), including support
   * for negative values.
   */
  historyRange: { start?: number; end?: number };

  /** Whether the range includes the end of the session (`end` is unset). */
  followTail: boolean;

  /**
   * If set, keep only the last N messages in memory and drop older messages as
   * new ones arrive.
   */
  maxMessages: number | null;
  eventsCursorId: string | null;
  listCursorEventId: string | null;
  dirty: boolean;
  dirtyReason: string | null;
  updatedAtMs: number | null;
  eventsStatus: PollingStatus;
  activeRequestId: string | null;
  readonly: boolean;
  snapshotId: string | null;
  streamingRow: StreamingRow | null;
  requestError: RequestErrorState | null;
}

function deriveWindowSettings(range: { start?: number; end?: number }): {
  followTail: boolean;
  maxMessages: number | null;
} {
  const followTail = range.end === undefined;
  const start = range.start;
  if (followTail && typeof start === 'number' && Number.isFinite(start) && start < 0) {
    return { followTail: true, maxMessages: Math.abs(start) };
  }
  return { followTail, maxMessages: null };
}

function trimTail(messages: IndexedMessage[], maxMessages: number | null): IndexedMessage[] {
  if (maxMessages == null) {
    return messages;
  }
  if (!Number.isFinite(maxMessages) || maxMessages <= 0) {
    return [];
  }
  if (messages.length <= maxMessages) {
    return messages;
  }
  return messages.slice(messages.length - maxMessages);
}

/**
 * The default history window: the last 50 messages (suffix range `-50:`).
 *
 * Used as the automatic fallback when a load for another range fails
 * because the range no longer selects any messages (for example after a
 * session compaction rewrote the history).
 */
export const DEFAULT_HISTORY_RANGE: { start?: number; end?: number } = {
  start: -50,
};

const RANGE_SELECTS_NO_MESSAGES_PATTERN = /range selects no messages/i;

/**
 * Detect the server's rejection of a message range that selects no
 * messages (HTTP 400 from `GET /sessions/{id}/messages`).
 *
 * Transports surface HTTP errors as `Error` objects whose message embeds
 * the server detail string, so the detail substring is matched on any
 * error-like value.
 */
export function isRangeSelectsNoMessagesError(err: unknown): boolean {
  if (typeof err === 'string') {
    return RANGE_SELECTS_NO_MESSAGES_PATTERN.test(err);
  }
  if (err && typeof err === 'object') {
    const message = (err as { message?: unknown }).message;
    if (typeof message === 'string') {
      return RANGE_SELECTS_NO_MESSAGES_PATTERN.test(message);
    }
  }
  return false;
}

function isDefaultHistoryRange(range: { start?: number; end?: number }): boolean {
  return range.start === DEFAULT_HISTORY_RANGE.start && range.end === undefined;
}

export class ChatController extends SimpleSubscribable<ChatControllerState> {
  private backend: AgentBackend;
  private eventSource: PollingEventSource | null = null;
  private readonly sessionId: string;
  private onEventsListener: ((events: Event[]) => void) | null = null;
  private rangeFallbackListener:
    | ((range: { start?: number; end?: number }) => void)
    | null = null;

  private epoch = 0;
  private autoReloadUsedEpoch = -1;
  private autoReloadInFlight = false;
  private cursorExpiryRecoveryInFlight = false;
  private lastLoadRange: { start?: number; end?: number } = {};
  private requestRevision = 0;
  private submissionRevision = 0;
  private completedRequestIds = new Set<string>();
  private disposed = false;

  constructor(options: {
    backend: AgentBackend;
    sessionId: string;
    initialMessages?: IndexedMessage[];
    initialEventsCursorId?: string | null;
    initialActiveRequestId?: string | null;
    onRangeFallback?: (range: { start?: number; end?: number }) => void;
  }) {
    super({
      sessionId: options.sessionId,
      loading: false,
      messages: options.initialMessages ?? [],
      historyRange: {},
      followTail: true,
      maxMessages: null,
      eventsCursorId: options.initialEventsCursorId ?? null,
      listCursorEventId: null,
      dirty: false,
      dirtyReason: null,
      updatedAtMs: null,
      eventsStatus: 'idle',
      activeRequestId: options.initialActiveRequestId ?? null,
      readonly: false,
      snapshotId: null,
      streamingRow: null,
      requestError: null,
    });
    this.backend = options.backend;
    this.sessionId = options.sessionId;
    this.rangeFallbackListener = options.onRangeFallback ?? null;

    // Default the window to the existing messages so we don't grow without
    // bounds when hydrating from cache. Frontends are expected to call
    // `setHistoryRangeFromRangeText` (or `loadMessagesFromRangeText`) to
    // configure a specific window such as "last 50".
    this.lastLoadRange = {};
  }

  dispose(): void {
    this.disposed = true;
    this.stopEventStreaming();
  }

  subscribe(listener: () => void): () => void {
    this.disposed = false;
    return super.subscribe(listener);
  }

  setEventsListener(listener: ((events: Event[]) => void) | null): void {
    this.onEventsListener = listener;
  }

  /**
   * Set (or clear) the listener notified when a message load falls back to
   * {@link DEFAULT_HISTORY_RANGE} because the requested range no longer
   * selects any messages. Consumers use it to sync their persisted range
   * state to the effective range.
   */
  setRangeFallbackListener(
    listener: ((range: { start?: number; end?: number }) => void) | null,
  ): void {
    this.rangeFallbackListener = listener;
  }

  isEventStreaming(): boolean {
    return this.eventSource != null;
  }

  clearRequestState(): void {
    const current = this.getSnapshot();
    this.setSnapshot({
      ...current,
      requestError: null,
      streamingRow: null,
    });
  }

  hydrateFromCache(options: {
    messages: IndexedMessage[];
    eventsCursorId: string | null;
    activeRequestId?: string | null;
    updatedAtMs?: number | null;
  }): void {
    const current = this.getSnapshot();
    if (current.loading) {
      return;
    }

    this.setSnapshot({
      ...current,
      messages: trimTail(options.messages, current.maxMessages),
      eventsCursorId: options.eventsCursorId,
      listCursorEventId: current.listCursorEventId,
      dirty: false,
      dirtyReason: null,
      updatedAtMs: options.updatedAtMs ?? current.updatedAtMs,
      activeRequestId: options.activeRequestId === undefined
        ? current.activeRequestId
        : options.activeRequestId,
      requestError: null,
      streamingRow: null,
    });
  }

  setHistoryRangeFromRangeText(options: { startText: string; endText: string }): void {
    const { start, end } = parseIndexRangeText({
      startText: options.startText,
      endText: options.endText,
    });
    this.setHistoryRange({ start, end });
  }

  setHistoryRange(range: { start?: number; end?: number }): void {
    const current = this.getSnapshot();
    const { followTail, maxMessages } = deriveWindowSettings(range);
    this.lastLoadRange = { ...range };
    this.setSnapshot({
      ...current,
      historyRange: { ...range },
      followTail,
      maxMessages,
      messages: trimTail(current.messages, maxMessages),
    });
  }

  getCacheSnapshot(): {
    messages: IndexedMessage[];
    eventsCursorId: string | null;
    activeRequestId: string | null;
    updatedAtMs: number | null;
  } {
    const snapshot = this.getSnapshot();
    return {
      messages: snapshot.messages,
      eventsCursorId: snapshot.eventsCursorId,
      activeRequestId: snapshot.activeRequestId,
      updatedAtMs: snapshot.updatedAtMs,
    };
  }

  async loadMessages(params?: { start?: number; end?: number }): Promise<void> {
    this.beginEpoch();
    const range = params ?? this.getSnapshot().historyRange ?? this.lastLoadRange;
    await this.reloadMessages(range, { bumpEpoch: false });
  }

  async loadMessagesFromRangeText(options: { startText: string; endText: string }): Promise<void> {
    const { start, end } = parseIndexRangeText({
      startText: options.startText,
      endText: options.endText,
    });
    this.beginEpoch();
    await this.reloadMessages({ start, end }, { bumpEpoch: false });
  }

  async recoverAfterResume(): Promise<void> {
    this.beginEpoch();
    const range = this.getSnapshot().historyRange ?? this.lastLoadRange;
    await this.reloadMessages(range, { bumpEpoch: false });
    await this.reconcileActiveRequest();
  }

  async recoverAfterCursorExpiry(): Promise<void> {
    if (this.cursorExpiryRecoveryInFlight) {
      return;
    }

    this.cursorExpiryRecoveryInFlight = true;
    this.beginEpoch();
    const range = this.getSnapshot().historyRange ?? this.lastLoadRange;
    try {
      await this.reloadMessages(range, { bumpEpoch: false });
      await this.reconcileActiveRequest();
    } catch (err) {
      this.setSnapshot({
        ...this.getSnapshot(),
        eventsStatus: 'expired',
      });
      throw err;
    } finally {
      this.cursorExpiryRecoveryInFlight = false;
    }
  }

  private async restartEventStreamingFromNullCursor(): Promise<void> {
    await this.reconcileActiveRequest();
    if (this.disposed) return;
    const current = this.getSnapshot();
    this.setSnapshot({
      ...current,
      eventsCursorId: null,
      listCursorEventId: null,
      eventsStatus: 'idle',
    });
    this.startEventStreaming({ initialSinceId: null });
  }

  private handleCursorExpiry(): void {
    const current = this.getSnapshot();
    const expiredSnapshotCursor =
      current.eventsCursorId != null &&
      current.eventsCursorId === current.listCursorEventId;

    if (expiredSnapshotCursor) {
      void this.restartEventStreamingFromNullCursor();
      return;
    }

    this.setSnapshot({
      ...current,
      eventsStatus: 'expired',
    });
    void this.recoverAfterCursorExpiry().catch(() => {
      // Keep the expired status visible if reload fails.
    });
  }

  ensureEventStreamingStarted(options: { initialSinceId?: string | null } = {}): void {
    const snapshot = this.getSnapshot();
    if (snapshot.loading || !snapshot.followTail || this.isEventStreaming()) {
      return;
    }

    const sinceId =
      options.initialSinceId ??
      snapshot.eventsCursorId ??
      this.getSnapshot().eventsCursorId ??
      null;
    this.startEventStreaming({ initialSinceId: sinceId });
  }

  async appendMessage(message: {
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    multipartContent?: any[] | null;
    metadata?: Record<string, any>;
  },
  options: { idempotencyKey?: string } = {}): Promise<void> {
    this.beginEpoch();
    await this.backend.appendMessage(this.sessionId, message, options);
  }

  async sendMessage(params: {
    message: {
      role: 'user' | 'assistant' | 'system' | 'tool';
      content: string;
      multipartContent?: any[] | null;
      metadata?: Record<string, any>;
    };
    configOverrides?: Record<string, any>;
    idempotencyKey?: string;
  }): Promise<void> {
    this.beginEpoch();
    const submission = ++this.submissionRevision;
    this.requestRevision += 1;
    const response = await this.backend.sendMessage(this.sessionId, params);
    await this.acknowledgeRequest(response?.request_id, submission);
  }

  async send(
    params: { configOverrides?: Record<string, any>; idempotencyKey?: string } = {},
  ): Promise<void> {
    this.beginEpoch();
    const submission = ++this.submissionRevision;
    this.requestRevision += 1;
    const response = await this.backend.send(this.sessionId, params);
    await this.acknowledgeRequest(response?.request_id, submission);
  }

  private async acknowledgeRequest(requestId: unknown, submission: number): Promise<void> {
    if (
      this.disposed ||
      submission !== this.submissionRevision ||
      typeof requestId !== 'string' ||
      !requestId.trim() ||
      this.completedRequestIds.has(requestId)
    ) return;
    const current = this.getSnapshot();
    this.requestRevision += 1;
    this.setSnapshot({ ...current, activeRequestId: requestId });
    await this.reconcileActiveRequest();
  }

  private async reconcileActiveRequest(): Promise<void> {
    if (this.disposed || !this.backend.getSessionRequestStatuses || this.getSnapshot().readonly) return;
    const revision = this.requestRevision;
    try {
      const response = await this.backend.getSessionRequestStatuses([this.sessionId]);
      if (this.disposed || revision !== this.requestRevision) return;
      const status = response?.statuses?.find(entry => entry.session_id === this.sessionId);
      if (!status) return;
      const activeRequestId = status.state === 'running' ? status.request_id : null;
      const current = this.getSnapshot();
      if (activeRequestId === current.activeRequestId) return;
      this.requestRevision += 1;
      this.setSnapshot({
        ...current,
        activeRequestId,
        streamingRow: current.streamingRow?.requestId === activeRequestId
          ? current.streamingRow
          : null,
      });
    } catch {
      return;
    }
  }

  async cancelActiveRequest(): Promise<void> {
    const active = this.getSnapshot().activeRequestId;
    if (!active) {
      return;
    }
    await this.backend.cancelRequest(active);
  }

  async softCancelActiveRequest(): Promise<void> {
    const active = this.getSnapshot().activeRequestId;
    if (!active) {
      return;
    }
    await this.backend.softCancelRequest(active);
  }

  async modifyMessage(index: number, content: string): Promise<void> {
    this.beginEpoch();
    await this.backend.modifyMessage(this.sessionId, index, content);
  }

  async deleteMessages(params: { indices?: number[]; range?: { start?: number; end?: number } }): Promise<void> {
    this.beginEpoch();
    await this.backend.deleteMessages(this.sessionId, params);
  }

  async deleteMessagesFromRangeText(options: { startText: string; endText: string }): Promise<void> {
    const { start, end } = parseIndexRangeText({
      startText: options.startText,
      endText: options.endText,
    });
    if (start === undefined && end === undefined) {
      throw new Error('Provide at least a start or end index.');
    }
    await this.deleteMessages({ range: { start, end } });
  }

  startEventStreaming(options: { initialSinceId: string | null } = { initialSinceId: null }): void {
    if (this.eventSource) {
      this.eventSource.stop();
      this.eventSource = null;
    }

    const source = new PollingEventSource(this.backend);
    this.eventSource = source;
    if (options.initialSinceId == null) {
      void this.reconcileActiveRequest();
    }
    source.start({
      sessionId: this.sessionId,
      initialSinceId: options.initialSinceId,
      onEvents: (events) => {
        if (this.onEventsListener) {
          this.onEventsListener(events);
        }
        this.applyEvents(events);

        const cursorId = source.getLastEventId();
        this.setSnapshot({
          ...this.getSnapshot(),
          eventsCursorId: cursorId ?? this.getSnapshot().eventsCursorId,
          eventsStatus: source.getStatus(),
          updatedAtMs: Date.now(),
        });
      },
      onCursorExpired: () => {
        this.handleCursorExpiry();
      },
    });
    this.setSnapshot({ ...this.getSnapshot(), eventsStatus: source.getStatus() });
  }

  stopEventStreaming(): void {
    if (this.eventSource) {
      this.eventSource.stop();
      this.eventSource = null;
    }
    this.setSnapshot({ ...this.getSnapshot(), eventsStatus: 'idle' });
  }

  private applyEvents(events: Event[]): void {
    if (!events || events.length === 0) return;

    const relevant = events.filter((ev) => (ev as any).session_id === this.sessionId);
    if (relevant.length === 0) return;

    let next = this.getSnapshot();

    // For non-tail slices (explicit end bound), history mutations cannot be
    // applied safely. We still apply streaming/request lifecycle updates.
    const applyHistory = next.followTail;

    for (const ev of relevant) {
      if (
        ev.type === 'request_started' ||
        ev.type === 'request_completed' ||
        ev.type === 'request_cancelled' ||
        ev.type === 'error'
      ) {
        this.requestRevision += 1;
        if (ev.type !== 'request_started' && typeof ev.request_id === 'string') {
          this.completedRequestIds.add(ev.request_id);
          if (this.completedRequestIds.size > 100) {
            this.completedRequestIds.delete(this.completedRequestIds.values().next().value!);
          }
        }
      }
      if (!next.dirty && applyHistory) {
        const history = reduceMessageHistoryWithOptions(next.messages, ev, {
          maxMessages: next.maxMessages,
          followTail: next.followTail,
        });

        if (history.kind === 'dirty') {
          next = {
            ...next,
            dirty: true,
            dirtyReason: next.dirtyReason ?? history.reason,
          };
          this.scheduleAutoReload('dirty');
        } else {
          next = {
            ...next,
            messages: history.messages,
          };
          if (history.needsBackfill) {
            this.scheduleAutoReload('backfill');
          }
        }
      }

      next = {
        ...next,
        ...reduceStreamingState(
          {
            activeRequestId: next.activeRequestId,
            requestError: next.requestError,
            streamingRow: next.streamingRow,
          },
          ev,
        ),
      };
    }

    this.setSnapshot(next);
  }

  private beginEpoch(): void {
    this.epoch += 1;
    this.autoReloadUsedEpoch = -1;
  }

  private scheduleAutoReload(reason: string): void {
    if (this.autoReloadInFlight) {
      return;
    }
    if (this.autoReloadUsedEpoch === this.epoch) {
      return;
    }
    const current = this.getSnapshot();
    if (current.loading) {
      return;
    }

    this.autoReloadUsedEpoch = this.epoch;
    this.autoReloadInFlight = true;

    const range = current.historyRange ?? this.lastLoadRange;
    void Promise.resolve()
      .then(() => this.reloadMessages(range, { bumpEpoch: false }))
      .catch(() => {
        // Reload failures are surfaced via the existing `dirty` banner.
      })
      .finally(() => {
        this.autoReloadInFlight = false;
      });
  }

  private async reloadMessages(
    range: { start?: number; end?: number },
    options: { bumpEpoch: boolean },
  ): Promise<void> {
    if (options.bumpEpoch) {
      this.beginEpoch();
    }
    await this.reloadMessagesWithRange(range, { allowFallback: true });
  }

  private async reloadMessagesWithRange(
    range: { start?: number; end?: number },
    options: { allowFallback: boolean },
  ): Promise<void> {
    const wasStreaming = this.isEventStreaming();
    if (wasStreaming) {
      this.stopEventStreaming();
    }

    const { followTail, maxMessages } = deriveWindowSettings(range);
    this.lastLoadRange = { ...range };

    this.setSnapshot({
      ...this.getSnapshot(),
      loading: true,
      historyRange: { ...range },
      followTail,
      maxMessages,
      messages: trimTail(this.getSnapshot().messages, maxMessages),
    });

    try {
      const revision = this.requestRevision;
      const {
        messages,
        cursorEventId,
        activeRequestId,
        readonly,
        snapshotId,
      } = await this.backend.listMessages(this.sessionId, range);

      if (this.disposed) return;
      const windowed = trimTail(messages, maxMessages);
      this.setSnapshot({
        ...this.getSnapshot(),
        loading: false,
        messages: windowed,
        eventsCursorId: cursorEventId,
        listCursorEventId: cursorEventId,
        dirty: false,
        dirtyReason: null,
        updatedAtMs: Date.now(),
        activeRequestId: revision === this.requestRevision
          ? (activeRequestId && this.completedRequestIds.has(activeRequestId) ? null : activeRequestId)
          : this.getSnapshot().activeRequestId,
        readonly: readonly === true,
        snapshotId: snapshotId ?? null,
        requestError: null,
        streamingRow: null,
      });

      const latest = this.getSnapshot();
      if (wasStreaming && latest.followTail) {
        this.startEventStreaming({ initialSinceId: cursorEventId ?? null });
      }
    } catch (err) {
      if (
        options.allowFallback &&
        !isDefaultHistoryRange(range) &&
        isRangeSelectsNoMessagesError(err)
      ) {
        // The requested range no longer selects any messages (for example
        // after a session compaction rewrote the history). Recover by
        // loading the default suffix window instead of failing.
        const fallbackRange = { ...DEFAULT_HISTORY_RANGE };
        if (this.rangeFallbackListener) {
          try {
            this.rangeFallbackListener(fallbackRange);
          } catch {
            // Listener errors must not break loading.
          }
        }
        await this.reloadMessagesWithRange(fallbackRange, {
          allowFallback: false,
        });
        return;
      }
      this.setSnapshot({ ...this.getSnapshot(), loading: false });
      throw err;
    }
  }
}
