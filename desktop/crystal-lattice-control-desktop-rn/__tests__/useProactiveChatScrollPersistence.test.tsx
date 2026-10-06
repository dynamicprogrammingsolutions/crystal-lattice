import { act, renderHook } from '@testing-library/react-native';
import type { NativeScrollEvent, NativeSyntheticEvent } from 'react-native';

import { useProactiveChatScrollPersistence } from '../src/chat/useProactiveChatScrollPersistence';

function scrollEvent(offsetY: number): NativeSyntheticEvent<NativeScrollEvent> {
  return {
    nativeEvent: {
      contentInset: { top: 0, left: 0, bottom: 0, right: 0 },
      contentOffset: { x: 0, y: offsetY },
      contentSize: { width: 800, height: 1000 },
      layoutMeasurement: { width: 800, height: 300 },
      zoomScale: 1,
    },
  } as NativeSyntheticEvent<NativeScrollEvent>;
}

describe('useProactiveChatScrollPersistence human activity', () => {
  it('reports stable native scroll movement and throttles repeated events', () => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-10-05T10:00:00.000Z'));
    const onUserScrollActivity = jest.fn();
    const { result, unmount } = renderHook(() =>
      useProactiveChatScrollPersistence({
        connectionId: 'connection-1',
        sessionId: 'session-1',
        cachedScrollAnchor: null,
        getMessagesForCache: () => [],
        onUpdateCache: jest.fn(),
        restoreReady: false,
        onUserScrollActivity,
      }),
    );

    act(() => {
      result.current.onScroll(scrollEvent(700));
      result.current.onScroll(scrollEvent(680));
      result.current.onScroll(scrollEvent(660));
    });
    expect(onUserScrollActivity).toHaveBeenCalledTimes(1);

    act(() => {
      jest.advanceTimersByTime(250);
      result.current.onScroll(scrollEvent(640));
    });
    expect(onUserScrollActivity).toHaveBeenCalledTimes(2);

    unmount();
    jest.useRealTimers();
  });
});
