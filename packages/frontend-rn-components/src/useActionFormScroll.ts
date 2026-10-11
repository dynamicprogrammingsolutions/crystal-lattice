import { useCallback, useEffect, useRef } from 'react';
import {
  Keyboard,
  ScrollView,
  TextInput,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';

export function useActionFormScroll() {
  const scrollRef = useRef<ScrollView | null>(null);
  const focusedInputRef = useRef<ReturnType<typeof TextInput.State.currentlyFocusedInput>>(null);
  const offsetRef = useRef(0);
  const frameRef = useRef<number | undefined>(undefined);

  const revealFocusedInput = useCallback(() => {
    const input = focusedInputRef.current;
    const scroll = scrollRef.current;
    if (!input || !scroll || TextInput.State.currentlyFocusedInput() !== input) {
      return;
    }
    input.measureInWindow((_inputX, inputY, _inputWidth, inputHeight) => {
      scroll
        .getNativeScrollRef()
        ?.measureInWindow((_scrollX, scrollY, _scrollWidth, scrollHeight) => {
          const padding = Math.min(8, Math.max(0, (scrollHeight - inputHeight) / 2));
          const top = scrollY + padding;
          const bottom = scrollY + scrollHeight - padding;
          const adjustment =
            inputY < top ? inputY - top : Math.max(0, inputY + inputHeight - bottom);
          if (adjustment !== 0) {
            scroll.scrollTo({
              y: Math.max(0, offsetRef.current + adjustment),
              animated: false,
            });
          }
        });
    });
  }, []);

  const scheduleReveal = useCallback(() => {
    if (frameRef.current !== undefined) cancelAnimationFrame(frameRef.current);
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = undefined;
      revealFocusedInput();
    });
  }, [revealFocusedInput]);

  useEffect(() => {
    const subscription = Keyboard.addListener('keyboardDidShow', scheduleReveal);
    return () => {
      subscription.remove();
      if (frameRef.current !== undefined) cancelAnimationFrame(frameRef.current);
    };
  }, [scheduleReveal]);

  return {
    scrollRef,
    onFieldFocus: () => {
      focusedInputRef.current = TextInput.State.currentlyFocusedInput();
      scheduleReveal();
    },
    onLayout: scheduleReveal,
    onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      offsetRef.current = event.nativeEvent.contentOffset.y;
    },
  };
}
