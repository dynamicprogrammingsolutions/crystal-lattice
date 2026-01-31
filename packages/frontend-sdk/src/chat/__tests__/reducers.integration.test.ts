import { describe, expect, it } from 'vitest';

import type { IndexedMessage } from '../../types/messages';
import { reduceMessageHistory } from '../messageHistoryReducer';
import { reduceStreamingState, type StreamingState } from '../streamingStateReducer';

type CombinedState = { messages: IndexedMessage[] } & StreamingState;

function reduceAll(state: CombinedState, event: any): CombinedState {
  return {
    ...state,
    messages: reduceMessageHistory(state.messages, event),
    ...reduceStreamingState(
      {
        activeRequestId: state.activeRequestId,
        requestError: state.requestError,
        streamingRow: state.streamingRow,
      },
      event,
    ),
  };
}

describe('message + streaming reducers composed', () => {
  it('handles a basic streamed request lifecycle', () => {
    const events = [
      { type: 'request_started', request_id: 'r1' },
      { type: 'assistant_message', phase: 'start', request_id: 'r1' },
      {
        type: 'partial',
        request_id: 'r1',
        message: { role: 'assistant', content: 'Hello', metadata: { reasoning: 'R1' } },
      },
      {
        type: 'final',
        request_id: 'r1',
        messages: [{ role: 'assistant', content: 'Hello!', metadata: null }],
      },
      { type: 'request_completed', request_id: 'r1' },
    ];

    let state: CombinedState = {
      messages: [],
      activeRequestId: null,
      requestError: null,
      streamingRow: null,
    };

    for (const ev of events) {
      state = reduceAll(state, ev);
    }

    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].message.content).toBe('Hello!');
    expect(state.streamingRow).toBeNull();
    expect(state.activeRequestId).toBeNull();
    expect(state.requestError).toBeNull();
  });
});
