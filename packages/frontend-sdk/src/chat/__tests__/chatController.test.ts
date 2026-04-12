import { describe, expect, it } from 'vitest';

import { ChatController } from '../chatController';

describe('ChatController.ensureEventStreamingStarted', () => {
  it('starts polling for tail-following sessions with an initial snapshot', () => {
    const controller = new ChatController({
      backend: {
        listEvents: async () => [],
      } as any,
      sessionId: 's1',
      initialMessages: [
        {
          index: 0,
          message: { role: 'user', content: 'hello' },
        },
      ] as any,
      initialEventsCursorId: '5',
    });

    controller.ensureEventStreamingStarted();

    expect(controller.isEventStreaming()).toBe(true);
    controller.dispose();
  });

  it('does not start polling for non-tail history windows', () => {
    const controller = new ChatController({
      backend: {
        listEvents: async () => [],
      } as any,
      sessionId: 's1',
      initialMessages: [
        {
          index: 0,
          message: { role: 'user', content: 'hello' },
        },
      ] as any,
      initialEventsCursorId: '5',
    });

    controller.setHistoryRange({ start: 0, end: 1 });
    controller.ensureEventStreamingStarted();

    expect(controller.isEventStreaming()).toBe(false);
  });
});