import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
  type RefObject,
} from 'react';

import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';

import type { MacTextViewHandle } from '../native/MacTextView';

type UpdateMessagesCache = (params: {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  composeText?: string;
}) => void;

export function usePersistedChatDraft(params: {
  connectionId: string;
  sessionId: string;
  cachedComposeText: string | null | undefined;
  getMessagesForCache: () => IndexedMessage[];
  onUpdateCache: UpdateMessagesCache;
  composerRef?: RefObject<MacTextViewHandle | null>;
  debounceMs?: number;
}): {
  composeText: string;
  setComposeText: (next: string) => void;
  composeTextRef: MutableRefObject<string>;
  handleChangeText: (text: string) => void;
  initialText: string;
} {
  const {
    connectionId,
    sessionId,
    cachedComposeText,
    getMessagesForCache,
    onUpdateCache,
    composerRef,
    debounceMs = 300,
  } = params;

  const initialText = useMemo(() => cachedComposeText ?? '', [cachedComposeText]);
  const [composeText, setComposeTextState] = useState<string>(initialText);
  const composeTextRef = useRef<string>(initialText);
  const dirtyRef = useRef(false);

  const didLogInitRef = useRef(false);

  const debugEnabled =
    (globalThis as any).CLC_DEBUG_DRAFT_PERSIST === true ||
    (globalThis as any).CLC_DEBUG_DRAFT_PERSIST === 'true';

  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const persistLatestRef = useRef<null | { connectionId: string; sessionId: string; composeText: string }>(
    null,
  );

  const flushPersist = useCallback(() => {
    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current);
      persistTimerRef.current = null;
    }
    const payload = persistLatestRef.current;
    if (!payload) {
      return;
    }
    persistLatestRef.current = null;

    if (debugEnabled) {
      console.log('[draftPersist] flush', {
        connectionId: payload.connectionId,
        sessionId: payload.sessionId,
        length: payload.composeText.length,
        dirty: dirtyRef.current,
      });
    }

    onUpdateCache({
      connectionId: payload.connectionId,
      sessionId: payload.sessionId,
      messages: getMessagesForCache(),
      composeText: payload.composeText,
    });
  }, [debugEnabled, getMessagesForCache, onUpdateCache]);

  const schedulePersist = useCallback(
    (nextText: string) => {
      persistLatestRef.current = { connectionId, sessionId, composeText: nextText };
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
      }
      persistTimerRef.current = setTimeout(() => {
        flushPersist();
      }, debounceMs);
    },
    [connectionId, debounceMs, flushPersist, sessionId],
  );

  const setComposeText = useCallback(
    (next: string) => {
      const resolved = String(next ?? '');
      composeTextRef.current = resolved;
      setComposeTextState(resolved);
      schedulePersist(resolved);
    },
    [schedulePersist],
  );

  const handleChangeText = useCallback(
    (text: string) => {
      dirtyRef.current = true;
      const next = String(text ?? '');
      composeTextRef.current = next;
      setComposeTextState(next);
      schedulePersist(next);
    },
    [schedulePersist],
  );

  useEffect(() => {
    if (!debugEnabled) {
      return;
    }
    if (didLogInitRef.current) {
      return;
    }
    didLogInitRef.current = true;
    console.log('[draftPersist] init', {
      connectionId,
      sessionId,
      cachedLength: (cachedComposeText ?? '').length,
    });
  }, [cachedComposeText, connectionId, debugEnabled, sessionId]);

  useEffect(() => {
    const nextCached = cachedComposeText ?? '';
    if (dirtyRef.current) {
      return;
    }
    if (nextCached === composeTextRef.current) {
      return;
    }

    if (debugEnabled) {
      console.log('[draftPersist] restore', {
        connectionId,
        sessionId,
        length: nextCached.length,
      });
    }

    composeTextRef.current = nextCached;
    setComposeTextState(nextCached);
    composerRef?.current?.setText(nextCached);
  }, [cachedComposeText, composerRef, connectionId, debugEnabled, sessionId]);

  useEffect(() => {
    return () => {
      flushPersist();
    };
  }, [flushPersist]);

  return {
    composeText,
    setComposeText,
    composeTextRef,
    handleChangeText,
    initialText,
  };
}
