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

  it('drops an expired snapshot cursor and restarts polling without reloading', async () => {
    let listEventsCalls = 0;
    let listMessagesCalls = 0;
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
            latestEventId: 'store:9',
            cursorExpired: false,
          };
        },
        getLatestEventId: async () => 'store:9',
        listMessages: async () => {
          listMessagesCalls += 1;
          return {
            messages: [
              { index: 0, message: { role: 'user', content: 'hello' } },
            ],
            cursorEventId: 'store:5',
            activeRequestId: null,
          };
        },
      } as any,
      sessionId: 's1',
      initialMessages: [] as any,
      initialEventsCursorId: null,
    });

    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
    expect(controller.getSnapshot().eventsCursorId).toBe('store:5');
    expect(controller.getSnapshot().listCursorEventId).toBe('store:5');

    controller.startEventStreaming({ initialSinceId: 'store:5' });
    await new Promise((resolve) => setTimeout(resolve, 25));

    const snapshot = controller.getSnapshot();
    expect(listMessagesCalls).toBe(1);
    expect(snapshot.messages.map((m) => m.message.content)).toEqual(['hello']);
    expect(snapshot.eventsStatus).toBe('running');
    expect(snapshot.eventsCursorId).toBeNull();
    expect(snapshot.listCursorEventId).toBeNull();
    controller.dispose();
  });
});