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

export class ChatController extends SimpleSubscribable<ChatControllerState> {
  private backend: AgentBackend;
  private eventSource: PollingEventSource | null = null;
  private readonly sessionId: string;
  private onEventsListener: ((events: Event[]) => void) | null = null;

  private epoch = 0;
  private autoReloadUsedEpoch = -1;
  private autoReloadInFlight = false;
  private cursorExpiryRecoveryInFlight = false;
  private lastLoadRange: { start?: number; end?: number } = {};

  constructor(options: {
    backend: AgentBackend;
    sessionId: string;
    initialMessages?: IndexedMessage[];
    initialEventsCursorId?: string | null;
    initialActiveRequestId?: string | null;
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
      streamingRow: null,
      requestError: null,
    });
    this.backend = options.backend;
    this.sessionId = options.sessionId;

    // Default the window to the existing messages so we don't grow without
    // bounds when hydrating from cache. Frontends are expected to call
    // `setHistoryRangeFromRangeText` (or `loadMessagesFromRangeText`) to
    // configure a specific window such as "last 50".
    this.lastLoadRange = {};
  }

  dispose(): void {
    this.stopEventStreaming();
  }

  setEventsListener(listener: ((events: Event[]) => void) | null): void {
    this.onEventsListener = listener;
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
      activeRequestId: options.activeRequestId ?? current.activeRequestId,
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
    const response = await this.backend.sendMessage(this.sessionId, params);

    const requestId = response?.request_id;
    if (typeof requestId === 'string' && requestId.trim()) {
      const current = this.getSnapshot();
      this.setSnapshot({
        ...current,
        activeRequestId: requestId,
      });
    }
  }

  async send(
    params: { configOverrides?: Record<string, any>; idempotencyKey?: string } = {},
  ): Promise<void> {
    this.beginEpoch();
    const response = await this.backend.send(this.sessionId, params);

    const requestId = response?.request_id;
    if (typeof requestId === 'string' && requestId.trim()) {
      const current = this.getSnapshot();
      this.setSnapshot({
        ...current,
        activeRequestId: requestId,
      });
    }
  }

  async cancelActiveRequest(): Promise<void> {
    const active = this.getSnapshot().activeRequestId;
    if (!active) {
      return;
    }
    await this.backend.cancelRequest(active);
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
        this.setSnapshot({
          ...this.getSnapshot(),
          eventsStatus: source.getStatus(),
        });
        void this.recoverAfterCursorExpiry().catch(() => {
          // Keep the expired status visible if reload fails.
        });
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
      const { messages, cursorEventId, activeRequestId } = await this.backend.listMessages(
        this.sessionId,
        range,
      );

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
        activeRequestId,
        requestError: null,
        streamingRow: null,
      });

      const latest = this.getSnapshot();
      if (wasStreaming && latest.followTail) {
        this.startEventStreaming({ initialSinceId: cursorEventId ?? null });
      }
    } catch (err) {
      this.setSnapshot({ ...this.getSnapshot(), loading: false });
      throw err;
    }
  }
}
