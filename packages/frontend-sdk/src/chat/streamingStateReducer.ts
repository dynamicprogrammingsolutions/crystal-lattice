import type { Event } from '../types/events';
import type { ApiMessage } from '../types/messages';

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

export interface StreamingState {
  activeRequestId: string | null;
  requestError: RequestErrorState | null;
  streamingRow: StreamingRow | null;
}

function mergeStreamingRowDelta(options: {
  prev: StreamingRow | null;
  requestId: string | null;
  reasoningDelta: string;
  contentDelta: string;
  rawMessage: ApiMessage;
}): StreamingRow {
  const base: StreamingRow =
    options.prev && (!options.requestId || options.prev.requestId === options.requestId)
      ? options.prev
      : {
          requestId: options.requestId || 'unknown',
          reasoning: '',
          content: '',
          metadata: null,
        };

  const nextReasoning = base.reasoning + options.reasoningDelta;
  const mergedMetadata = {
    ...(base.metadata || {}),
    ...(options.rawMessage.metadata || {}),
    reasoning: nextReasoning,
  } as Record<string, any>;

  return {
    requestId: base.requestId,
    reasoning: nextReasoning,
    content: base.content + options.contentDelta,
    metadata: mergedMetadata,
  };
}

export function reduceStreamingState(state: StreamingState, event: Event): StreamingState {
  const type = (event as any).type;

  if (type === 'request_started') {
    const rid = typeof (event as any).request_id === 'string' ? (event as any).request_id : null;
    return {
      ...state,
      activeRequestId: rid || state.activeRequestId,
      requestError: null,
      streamingRow: null,
    };
  }

  if (type === 'assistant_message') {
    const phase = (event as any).phase;
    if (phase !== 'start') {
      return state;
    }

    const rid = typeof (event as any).request_id === 'string' ? (event as any).request_id : null;
    const requestId = typeof (event as any).request_id === 'string' ? (event as any).request_id : 'unknown';
    return {
      ...state,
      activeRequestId: state.activeRequestId || rid,
      streamingRow: {
        requestId,
        reasoning: '',
        content: '',
        metadata: null,
      },
    };
  }

  if (type === 'partial') {
    const rawMessage = ((event as any).message || {}) as ApiMessage;
    const rawMetadata = (rawMessage.metadata || {}) as Record<string, any>;
    const reasoningDelta = typeof rawMetadata.reasoning === 'string' ? rawMetadata.reasoning : '';
    const contentDelta = typeof rawMessage.content === 'string' ? rawMessage.content : '';
    if (!reasoningDelta && !contentDelta) {
      return state;
    }

    const evRequestId = (event as any).request_id ?? null;
    const requestId = typeof evRequestId === 'string' ? evRequestId : null;

    const nextActiveRequestId = state.activeRequestId || requestId;

    return {
      ...state,
      activeRequestId: nextActiveRequestId,
      streamingRow: mergeStreamingRowDelta({
        prev: state.streamingRow,
        requestId,
        reasoningDelta,
        contentDelta,
        rawMessage,
      }),
    };
  }

  if (type === 'final') {
    return {
      ...state,
      streamingRow: null,
    };
  }

  if (type === 'error') {
    const detail =
      (typeof (event as any).detail === 'string' && (event as any).detail) || 'Request failed with an error.';
    const requestId = typeof (event as any).request_id === 'string' ? (event as any).request_id : null;
    return { ...state, requestError: { detail, requestId } };
  }

  if (type === 'request_completed' || type === 'request_cancelled') {
    const rid = (event as any).request_id;
    const current = state.activeRequestId;
    return {
      ...state,
      activeRequestId: current == null || current === rid ? null : current,
    };
  }

  return state;
}
