import { describe, expect, it } from 'vitest';

import { ChatController } from '../chatController';

describe('ChatController.ensureEventStreamingStarted', () => {
  it('starts polling for tail-following sessions with an initial snapshot', () => {
    const controller = new ChatController({
      backend: {
        listEvents: async () => ({ events: [], latestEventId: null, cursorExpired: false }),
        getLatestEventId: async () => null,
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
        listEvents: async () => ({ events: [], latestEventId: null, cursorExpired: false }),
        getLatestEventId: async () => null,
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

  it('reloads automatically when the polling cursor expires', async () => {
    let listEventsCalls = 0;
    const controller = new ChatController({
      backend: {
        listEvents: async () => {
          listEventsCalls += 1;
          if (listEventsCalls === 1) {
            return {
              events: [],
              latestEventId: 'store:9',
              cursorExpired: true,
            };
          }
          return {
            events: [],
            latestEventId: 'store:11',
            cursorExpired: false,
          };
        },
        getLatestEventId: async () => 'store:9',
        listMessages: async () => ({
          messages: [
            { index: 0, message: { role: 'user', content: 'hello' } },
            { index: 1, message: { role: 'assistant', content: 'reloaded' } },
          ],
          cursorEventId: 'store:11',
          activeRequestId: null,
        }),
      } as any,
      sessionId: 's1',
      initialMessages: [
        {
          index: 0,
          message: { role: 'user', content: 'cached' },
        },
      ] as any,
      initialEventsCursorId: 'store:1',
    });

    controller.startEventStreaming({ initialSinceId: 'store:1' });
    await new Promise((resolve) => setTimeout(resolve, 25));

    const snapshot = controller.getSnapshot();
    expect(snapshot.messages.some((m) => m.message.content === 'reloaded')).toBe(true);
    expect(snapshot.eventsStatus).toBe('running');
    expect(snapshot.eventsCursorId).toBe('store:11');
    controller.dispose();
  });
});