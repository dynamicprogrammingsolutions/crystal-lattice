import { describe, expect, it } from 'vitest';

import { reduceStreamingState, type StreamingState } from '../streamingStateReducer';

function emptyState(): StreamingState {
  return {
    activeRequestId: null,
    requestError: null,
    streamingRow: null,
  };
}

describe('reduceStreamingState', () => {
  it('request_started sets activeRequestId and clears streaming/error state', () => {
    const initial: StreamingState = {
      activeRequestId: null,
      requestError: { detail: 'oops', requestId: 'r0' },
      streamingRow: { requestId: 'r0', reasoning: 'x', content: 'y', metadata: { a: 1 } },
    };

    const next = reduceStreamingState(initial, {
      type: 'request_started',
      request_id: 'r1',
    } as any);

    expect(next.activeRequestId).toBe('r1');
    expect(next.requestError).toBeNull();
    expect(next.streamingRow).toBeNull();
  });

  it('assistant_message start initializes streamingRow', () => {
    const next = reduceStreamingState(emptyState(), {
      type: 'assistant_message',
      phase: 'start',
      request_id: 'r1',
    } as any);

    expect(next.activeRequestId).toBe('r1');
    expect(next.streamingRow?.requestId).toBe('r1');
    expect(next.streamingRow?.reasoning).toBe('');
    expect(next.streamingRow?.content).toBe('');
  });

  it('partial accumulates reasoning/content deltas', () => {
    const started = reduceStreamingState(emptyState(), {
      type: 'assistant_message',
      phase: 'start',
      request_id: 'r1',
    } as any);

    const afterFirst = reduceStreamingState(started, {
      type: 'partial',
      request_id: 'r1',
      message: { role: 'assistant', content: 'Hello', metadata: { reasoning: 'R1' } },
    } as any);

    const afterSecond = reduceStreamingState(afterFirst, {
      type: 'partial',
      request_id: 'r1',
      message: { role: 'assistant', content: ' world', metadata: { reasoning: 'R2' } },
    } as any);

    expect(afterSecond.streamingRow?.content).toBe('Hello world');
    expect(afterSecond.streamingRow?.reasoning).toBe('R1R2');
    expect(afterSecond.streamingRow?.metadata?.reasoning).toBe('R1R2');
  });

  it('final clears streamingRow and keeps activeRequestId until completion', () => {
    const state: StreamingState = {
      activeRequestId: 'r1',
      requestError: null,
      streamingRow: { requestId: 'r1', reasoning: 'x', content: 'y', metadata: null },
    };

    const next = reduceStreamingState(state, { type: 'final', request_id: 'r1' } as any);
    expect(next.streamingRow).toBeNull();
    expect(next.activeRequestId).toBe('r1');
  });

  it('request_completed clears activeRequestId when matching', () => {
    const state: StreamingState = { ...emptyState(), activeRequestId: 'r1' };
    const next = reduceStreamingState(state, { type: 'request_completed', request_id: 'r1' } as any);
    expect(next.activeRequestId).toBeNull();
  });

  it('request_completed keeps activeRequestId when not matching', () => {
    const state: StreamingState = { ...emptyState(), activeRequestId: 'r2' };
    const next = reduceStreamingState(state, { type: 'request_completed', request_id: 'r1' } as any);
    expect(next.activeRequestId).toBe('r2');
  });

  it('captures request errors', () => {
    const next = reduceStreamingState(emptyState(), {
      type: 'error',
      request_id: 'r1',
      detail: 'boom',
    } as any);

    expect(next.requestError?.detail).toBe('boom');
    expect(next.requestError?.requestId).toBe('r1');
  });
});
