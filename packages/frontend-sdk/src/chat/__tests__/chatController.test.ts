import { describe, expect, it, vi } from 'vitest';

import { ChatController } from '../chatController';

const RANGE_ERROR = new Error(
  'HTTP 400 GET /sessions/s1/messages?start=100&end=150: range selects no messages',
);

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

  it('retains read-only snapshot context from a message-list response', async () => {
    const controller = new ChatController({
      backend: {
        listMessages: async () => ({
          messages: [
            { index: 0, message: { role: 'user', content: 'snapshot message' } },
          ],
          cursorEventId: 'store:5',
          activeRequestId: null,
          readonly: true,
          snapshotId: 'snapshot:1',
        }),
      } as any,
      sessionId: 's1',
    });

    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });

    expect(controller.getSnapshot()).toMatchObject({
      readonly: true,
      snapshotId: 'snapshot:1',
    });
  });
});

describe('ChatController default-range fallback', () => {
  it('falls back to the default range when an absolute range selects no messages', async () => {
    const listMessages = vi
      .fn()
      .mockRejectedValueOnce(RANGE_ERROR)
      .mockResolvedValueOnce({
        messages: [
          { index: 0, message: { role: 'user', content: 'summary' } },
          { index: 1, message: { role: 'assistant', content: 'reply' } },
        ],
        cursorEventId: 'store:5',
        activeRequestId: null,
      });
    const onRangeFallback = vi.fn();
    const controller = new ChatController({
      backend: { listMessages } as any,
      sessionId: 's1',
      onRangeFallback,
    });

    await controller.loadMessagesFromRangeText({
      startText: '100',
      endText: '150',
    });

    expect(listMessages).toHaveBeenCalledTimes(2);
    expect(listMessages).toHaveBeenNthCalledWith(1, 's1', {
      start: 100,
      end: 150,
    });
    expect(listMessages).toHaveBeenNthCalledWith(2, 's1', { start: -50 });

    const snapshot = controller.getSnapshot();
    expect(snapshot.historyRange).toEqual({ start: -50 });
    expect(snapshot.followTail).toBe(true);
    expect(snapshot.maxMessages).toBe(50);
    expect(snapshot.messages).toHaveLength(2);
    expect(snapshot.loading).toBe(false);
    expect(onRangeFallback).toHaveBeenCalledTimes(1);
    expect(onRangeFallback).toHaveBeenCalledWith({ start: -50 });
    controller.dispose();
  });

  it('notifies a listener set after construction', async () => {
    const listMessages = vi
      .fn()
      .mockRejectedValueOnce(RANGE_ERROR)
      .mockResolvedValueOnce({ messages: [], cursorEventId: null });
    const controller = new ChatController({
      backend: { listMessages } as any,
      sessionId: 's1',
    });
    const onRangeFallback = vi.fn();
    controller.setRangeFallbackListener(onRangeFallback);

    await controller.loadMessagesFromRangeText({
      startText: '100',
      endText: '150',
    });

    expect(onRangeFallback).toHaveBeenCalledWith({ start: -50 });
    controller.dispose();
  });

  it('does not fall back for non-range failures', async () => {
    const listMessages = vi
      .fn()
      .mockRejectedValueOnce(new Error('HTTP 500 GET /sessions/s1/messages: boom'));
    const controller = new ChatController({
      backend: { listMessages } as any,
      sessionId: 's1',
    });

    await expect(
      controller.loadMessagesFromRangeText({ startText: '100', endText: '150' }),
    ).rejects.toThrow('boom');
    expect(listMessages).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot().historyRange).toEqual({
      start: 100,
      end: 150,
    });
    controller.dispose();
  });

  it('does not retry the fallback when the default range itself fails', async () => {
    const listMessages = vi.fn().mockRejectedValue(RANGE_ERROR);
    const controller = new ChatController({
      backend: { listMessages } as any,
      sessionId: 's1',
    });

    await expect(
      controller.loadMessagesFromRangeText({ startText: '-50', endText: '' }),
    ).rejects.toThrow(RANGE_ERROR);
    expect(listMessages).toHaveBeenCalledTimes(1);
    controller.dispose();
  });
});