import type { AgentBackend } from '../backend/backend';
import type {
  AssistantMessageEvent,
  ErrorEvent,
  Event,
  FinalEvent,
  MessageAppendedEvent,
  PartialEvent,
  ToolResultsEvent,
} from '../types/events';
import type { ApiMessage, IndexedMessage } from '../types/messages';
import { PollingEventSource, type PollingStatus } from '../events/pollingEventSource';
import { SimpleSubscribable } from '../util/subscribable';

export interface StreamingRow {
  requestId: string;
  reasoning: string;
  content: string;
  metadata: Record<string, any> | null;
}

export interface RequestErrorState {
  detail: string;
  requestId: string | null;
}

export interface ChatControllerState {
  sessionId: string;
  loading: boolean;
  messages: IndexedMessage[];
  cursorEventId: string | null;
  lastEventId: string | null;
  eventsStatus: PollingStatus;
  activeRequestId: string | null;
  streamingRow: StreamingRow | null;
  requestError: RequestErrorState | null;
}

export class ChatController extends SimpleSubscribable<ChatControllerState> {
  private backend: AgentBackend;
  private eventSource: PollingEventSource | null = null;
  private readonly sessionId: string;

  constructor(options: { backend: AgentBackend; sessionId: string }) {
    super({
      sessionId: options.sessionId,
      loading: false,
      messages: [],
      cursorEventId: null,
      lastEventId: null,
      eventsStatus: 'idle',
      activeRequestId: null,
      streamingRow: null,
      requestError: null,
    });
    this.backend = options.backend;
    this.sessionId = options.sessionId;
  }

  dispose(): void {
    this.stopEventStreaming();
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
        cursorEventId,
        lastEventId: cursorEventId,
        activeRequestId,
        streamingRow: null,
      });
    } catch (err) {
      this.setSnapshot({ ...this.getSnapshot(), loading: false });
      throw err;
    }
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
        this.applyEvents(events);
        this.setSnapshot({
          ...this.getSnapshot(),
          lastEventId: source.getLastEventId(),
          eventsStatus: source.getStatus(),
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

    for (const ev of relevant) {
      const type = (ev as any).type;

      if (type === 'request_started') {
        const rid = typeof (ev as any).request_id === 'string' ? (ev as any).request_id : null;
        if (rid) {
          this.setSnapshot({ ...this.getSnapshot(), activeRequestId: rid });
        }
        this.setSnapshot({ ...this.getSnapshot(), requestError: null, streamingRow: null });
      } else if (type === 'assistant_message') {
        const msgEv = ev as AssistantMessageEvent;
        if ((msgEv as any).phase === 'start') {
          const rid = typeof (msgEv as any).request_id === 'string' ? (msgEv as any).request_id : null;
          if (rid) {
            const current = this.getSnapshot().activeRequestId;
            if (!current) {
              this.setSnapshot({ ...this.getSnapshot(), activeRequestId: rid });
            }
          }
          this.setSnapshot({
            ...this.getSnapshot(),
            streamingRow: {
              requestId: (msgEv as any).request_id ?? 'unknown',
              reasoning: '',
              content: '',
              metadata: null,
            },
          });
        }
      } else if (type === 'partial') {
        this.applyPartialEvent(ev as PartialEvent);
      } else if (type === 'final') {
        this.applyFinalEvent(ev as FinalEvent);
        this.setSnapshot({ ...this.getSnapshot(), streamingRow: null });
      } else if (type === 'message_appended') {
        this.applyMessageAppendedEvent(ev as MessageAppendedEvent);
      } else if (type === 'tool_results') {
        this.applyToolResultsEvent(ev as ToolResultsEvent);
      } else if (type === 'error') {
        const errEv = ev as ErrorEvent;
        const detail =
          (typeof (errEv as any).detail === 'string' && (errEv as any).detail) ||
          'Request failed with an error.';
        this.setSnapshot({
          ...this.getSnapshot(),
          requestError: { detail, requestId: (errEv as any).request_id ?? null },
        });
      } else if (type === 'request_completed' || type === 'request_cancelled') {
        const rid = (ev as any).request_id;
        const current = this.getSnapshot().activeRequestId;
        this.setSnapshot({
          ...this.getSnapshot(),
          activeRequestId: current == null || current === rid ? null : current,
        });
      }
    }
  }

  private applyFinalEvent(ev: FinalEvent): void {
    const nextMessages = Array.isArray((ev as any).messages) ? (ev as any).messages : [];
    if (nextMessages.length === 0) return;

    const current = this.getSnapshot();
    const updated = [...current.messages];
    let lastIndex = updated.length > 0 ? updated[updated.length - 1].index : -1;
    for (const msg of nextMessages) {
      if (!msg) continue;
      lastIndex += 1;
      updated.push({ index: lastIndex, message: msg as ApiMessage });
    }
    this.setSnapshot({ ...current, messages: updated });
  }

  private applyMessageAppendedEvent(ev: MessageAppendedEvent): void {
    const message = (ev as any).message;
    if (!message) return;

    const current = this.getSnapshot();
    const lastIndex = current.messages.length > 0 ? current.messages[current.messages.length - 1].index : -1;
    this.setSnapshot({
      ...current,
      messages: [...current.messages, { index: lastIndex + 1, message }],
    });
  }

  private applyToolResultsEvent(ev: ToolResultsEvent): void {
    const nextMessages = Array.isArray((ev as any).messages) ? (ev as any).messages : [];
    if (nextMessages.length === 0) return;

    const current = this.getSnapshot();
    const updated = [...current.messages];
    let lastIndex = updated.length > 0 ? updated[updated.length - 1].index : -1;
    for (const msg of nextMessages) {
      if (!msg) continue;
      lastIndex += 1;
      updated.push({ index: lastIndex, message: msg as ApiMessage });
    }
    this.setSnapshot({ ...current, messages: updated });
  }

  private applyPartialEvent(ev: PartialEvent): void {
    const rawMessage = ((ev as any).message || {}) as ApiMessage;
    const rawMetadata = (rawMessage.metadata || {}) as Record<string, any>;
    const reasoningDelta = typeof rawMetadata.reasoning === 'string' ? rawMetadata.reasoning : '';
    const contentDelta = typeof rawMessage.content === 'string' ? rawMessage.content : '';
    if (!reasoningDelta && !contentDelta) return;

    const evRequestId = (ev as any).request_id ?? null;
    if (typeof evRequestId === 'string' && evRequestId) {
      const currentActive = this.getSnapshot().activeRequestId;
      if (!currentActive) {
        this.setSnapshot({ ...this.getSnapshot(), activeRequestId: evRequestId });
      }
    }

    const current = this.getSnapshot();
    const prev = current.streamingRow;
    const base: StreamingRow =
      prev && (!evRequestId || prev.requestId === evRequestId)
        ? prev
        : {
            requestId: evRequestId || 'unknown',
            reasoning: '',
            content: '',
            metadata: null,
          };
    const nextReasoning = base.reasoning + reasoningDelta;
    const mergedMetadata = {
      ...(base.metadata || {}),
      ...(rawMessage.metadata || {}),
      reasoning: nextReasoning,
    } as Record<string, any>;

    this.setSnapshot({
      ...current,
      streamingRow: {
        requestId: base.requestId,
        reasoning: nextReasoning,
        content: base.content + contentDelta,
        metadata: mergedMetadata,
      },
    });
  }
}
