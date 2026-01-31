import type { AgentBackend } from '../backend/backend';
import type { Event } from '../types/events';
import type { IndexedMessage } from '../types/messages';
import { parseIndexRangeText } from '../utils/range';
import { PollingEventSource, type PollingStatus } from '../events/pollingEventSource';
import { SimpleSubscribable } from '../util/subscribable';
import { reduceMessageHistory } from './messageHistoryReducer';
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

export class ChatController extends SimpleSubscribable<ChatControllerState> {
  private backend: AgentBackend;
  private eventSource: PollingEventSource | null = null;
  private readonly sessionId: string;
  private onEventsListener: ((events: Event[]) => void) | null = null;

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
      messages: options.messages,
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
    this.setSnapshot({ ...this.getSnapshot(), loading: true });
    try {
      const { messages, cursorEventId, activeRequestId } = await this.backend.listMessages(
        this.sessionId,
        params,
      );

      this.setSnapshot({
        ...this.getSnapshot(),
        loading: false,
        messages,
        eventsCursorId: cursorEventId,
        listCursorEventId: cursorEventId,
        dirty: false,
        dirtyReason: null,
        updatedAtMs: Date.now(),
        activeRequestId,
        streamingRow: null,
      });
    } catch (err) {
      this.setSnapshot({ ...this.getSnapshot(), loading: false });
      throw err;
    }
  }

  async loadMessagesFromRangeText(options: { startText: string; endText: string }): Promise<void> {
    const { start, end } = parseIndexRangeText({
      startText: options.startText,
      endText: options.endText,
    });
    await this.loadMessages({ start, end });
  }

  async appendMessage(message: {
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    metadata?: Record<string, any>;
  }): Promise<void> {
    await this.backend.appendMessage(this.sessionId, message);
  }

  async send(params?: { configOverrides?: Record<string, any> }): Promise<void> {
    await this.backend.send(this.sessionId, params);
  }

  async cancelActiveRequest(): Promise<void> {
    const active = this.getSnapshot().activeRequestId;
    if (!active) {
      return;
    }
    await this.backend.cancelRequest(active);
  }

  async modifyMessage(index: number, content: string): Promise<void> {
    await this.backend.modifyMessage(this.sessionId, index, content);
  }

  async deleteMessages(params: { indices?: number[]; range?: { start?: number; end?: number } }): Promise<void> {
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

    for (const ev of relevant) {
      if (!next.dirty) {
        const history = reduceMessageHistory(next.messages, ev);
        if (history.kind === 'dirty') {
          next = {
            ...next,
            dirty: true,
            dirtyReason: next.dirtyReason ?? history.reason,
          };
        } else {
          next = {
            ...next,
            messages: history.messages,
          };
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
}
