import {
  describePendingRequestRecovery,
  shouldClearPendingRequestRecovery,
  type PendingRequestRecovery,
} from '../src/chatRecovery';

describe('chatRecovery helpers', () => {
  test('describePendingRequestRecovery summarizes multipart sends without text', () => {
    const pending: PendingRequestRecovery = {
      kind: 'send_message',
      idempotencyKey: 'idem-1',
      requestedAtMs: 1,
      errorMessage: 'timeout',
      message: {
        role: 'user',
        content: '',
        multipartContent: [{ type: 'image', content: { url: 'data:' } }],
      },
    };

    expect(describePendingRequestRecovery(pending)).toBe('Multipart message (1 part)');
  });

  test('shouldClearPendingRequestRecovery only clears when the server exposes a request id', () => {
    const pending: PendingRequestRecovery = {
      kind: 'send',
      idempotencyKey: 'idem-2',
      requestedAtMs: 2,
      errorMessage: 'timeout',
    };

    expect(
      shouldClearPendingRequestRecovery({
        pending,
        activeRequestId: null,
      }),
    ).toBe(false);

    expect(
      shouldClearPendingRequestRecovery({
        pending,
        activeRequestId: 'req-123',
      }),
    ).toBe(true);
  });
});