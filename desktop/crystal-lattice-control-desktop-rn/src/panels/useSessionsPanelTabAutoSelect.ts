import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type RefObject,
} from 'react';
import type { LayoutChangeEvent } from 'react-native';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';

const AUTOSELECT_TTL_MS = 1500;
const VISIBILITY_MARGIN_TOP_PX = 12;
const VISIBILITY_MARGIN_BOTTOM_PX = 12;

export type ActiveTabSelection = {
  tabId: string | null;
  connectionId: string | null;
  sessionId: string | null;
};

type PendingTabSelect = {
  tabId: string;
  sessionId: string;
  armedAtMs: number;
};

export function useSessionsPanelTabAutoSelect(params: {
  connectionId: string | null;
  visibleSessionIds: readonly string[];
  activeTab: ActiveTabSelection;
  enabled: boolean;
}): {
  selectedSessionId: string | null;
  onUserSelectSessionId: (sessionId: string) => void;
  scrollViewRef: RefObject<any>;
  getRowLayoutHandler: (sessionId: string) => (event: LayoutChangeEvent) => void;
} {
  const { connectionId, visibleSessionIds, activeTab, enabled } = params;

  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingTabSelect | null>(null);
  const [layoutVersion, setLayoutVersion] = useState(0);

  const scrollViewRef = useRef<any>(null);
  const rowLayoutsRef = useRef<Record<string, { y: number; height: number }>>({});

  const lastTabIdRef = useRef<string | null>(null);

  const visibleSet = useMemo(() => new Set(visibleSessionIds), [visibleSessionIds]);

  const ensureRowFullyVisible = useCallback(
    async (sessionId: string) => {
      const layout = rowLayoutsRef.current[sessionId];
      if (!layout) {
        return;
      }

      const metrics = await getMacScrollViewMetrics(scrollViewRef.current);
      if (!metrics) {
        return;
      }

      const viewportHeight = metrics.viewportHeight;
      if (!Number.isFinite(viewportHeight) || viewportHeight <= 0) {
        return;
      }

      const rowTop = layout.y;
      const rowBottom = layout.y + layout.height;

      const visibleTop = metrics.offsetY + VISIBILITY_MARGIN_TOP_PX;
      const visibleBottom = metrics.offsetY + viewportHeight - VISIBILITY_MARGIN_BOTTOM_PX;

      const fullyVisible = rowTop >= visibleTop && rowBottom <= visibleBottom;
      if (fullyVisible) {
        return;
      }

      let targetOffset = metrics.offsetY;
      if (rowTop < visibleTop) {
        targetOffset = rowTop - VISIBILITY_MARGIN_TOP_PX;
      } else if (rowBottom > visibleBottom) {
        targetOffset = rowBottom + VISIBILITY_MARGIN_BOTTOM_PX - viewportHeight;
      }

      const maxOffset = Math.max(0, metrics.contentHeight - viewportHeight);
      const clamped = Math.max(0, Math.min(maxOffset, Math.round(targetOffset)));
      scrollViewRef.current?.scrollTo?.({ y: clamped, animated: true });
    },
    [],
  );

  const onUserSelectSessionId = useCallback(
    (sessionId: string) => {
      setSelectedSessionId(sessionId);
      ensureRowFullyVisible(sessionId).catch(() => {});
    },
    [ensureRowFullyVisible],
  );

  useEffect(() => {
    // Reset local selection when switching connections.
    setSelectedSessionId(null);
  }, [connectionId]);

  useEffect(() => {
    const nextTabId = activeTab.tabId;
    if (!enabled) {
      lastTabIdRef.current = nextTabId;
      setPending(null);
      return;
    }

    if (!nextTabId || nextTabId === lastTabIdRef.current) {
      return;
    }

    lastTabIdRef.current = nextTabId;

    if (!activeTab.sessionId) {
      setPending(null);
      return;
    }

    setPending({ tabId: nextTabId, sessionId: activeTab.sessionId, armedAtMs: Date.now() });
  }, [activeTab.sessionId, activeTab.tabId, enabled]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    if (!pending) {
      return;
    }
    if (!connectionId) {
      return;
    }

    if (Date.now() - pending.armedAtMs > AUTOSELECT_TTL_MS) {
      setPending(null);
      return;
    }

    // Only apply when SessionsPanel is showing the active tab's connection.
    if (activeTab.connectionId !== connectionId) {
      return;
    }

    const sessionId = pending.sessionId;
    if (!visibleSet.has(sessionId)) {
      return;
    }

    // Apply selection once.
    setSelectedSessionId(sessionId);
    setPending(null);
    ensureRowFullyVisible(sessionId).catch(() => {});
    // layoutVersion is used to retry when rows mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab.connectionId, connectionId, enabled, ensureRowFullyVisible, layoutVersion, pending, visibleSet]);

  const getRowLayoutHandler = useCallback(
    (sessionId: string) => {
      return (event: LayoutChangeEvent) => {
        const y = Number(event.nativeEvent?.layout?.y ?? NaN);
        const height = Number(event.nativeEvent?.layout?.height ?? NaN);
        if (!Number.isFinite(y) || !Number.isFinite(height)) {
          return;
        }

        const existing = rowLayoutsRef.current[sessionId];
        const changed =
          !existing ||
          Math.abs(existing.y - y) > 0.5 ||
          Math.abs(existing.height - height) > 0.5;
        if (!changed) {
          return;
        }

        rowLayoutsRef.current[sessionId] = { y, height };
        setLayoutVersion((prev) => prev + 1);
      };
    },
    [],
  );

  return {
    selectedSessionId,
    onUserSelectSessionId,
    scrollViewRef,
    getRowLayoutHandler,
  };
}
