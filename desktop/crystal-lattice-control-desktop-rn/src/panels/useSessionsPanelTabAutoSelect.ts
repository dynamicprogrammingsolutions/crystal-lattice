import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
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
  intentKey: string;
  tabId: string;
  sessionId: string;
  armedAtMs: number;
};

export type SessionsPanelSelection = {
  sessionId: string;
  source: 'manual' | 'activeTab';
  tabId?: string;
};

export type SessionsPanelSelectionState = {
  connectionId: string | null;
  activeTab: ActiveTabSelection;
  enabled: boolean;
  followIntentKey: string | null;
  selection: SessionsPanelSelection | null;
  pending: PendingTabSelect | null;
};

export type SessionsPanelSelectionAction =
  | {
      type: 'reconcile';
      connectionId: string | null;
      activeTab: ActiveTabSelection;
      enabled: boolean;
      nowMs: number;
    }
  | {
      type: 'manualSelect';
      sessionId: string;
    }
  | {
      type: 'applyPending';
      intentKey: string;
      nowMs: number;
    };

export const INITIAL_SESSIONS_PANEL_SELECTION_STATE: SessionsPanelSelectionState =
  {
    connectionId: null,
    activeTab: {
      tabId: null,
      connectionId: null,
      sessionId: null,
    },
    enabled: false,
    followIntentKey: null,
    selection: null,
    pending: null,
  };

function activeTabsEqual(
  left: ActiveTabSelection,
  right: ActiveTabSelection,
): boolean {
  return (
    left.tabId === right.tabId &&
    left.connectionId === right.connectionId &&
    left.sessionId === right.sessionId
  );
}

function resolveFollowIntent(
  connectionId: string | null,
  activeTab: ActiveTabSelection,
  enabled: boolean,
): { key: string; tabId: string; sessionId: string } | null {
  if (
    !enabled ||
    !connectionId ||
    !activeTab.tabId ||
    !activeTab.connectionId ||
    !activeTab.sessionId ||
    activeTab.connectionId !== connectionId
  ) {
    return null;
  }
  return {
    key: JSON.stringify([
      activeTab.tabId,
      activeTab.connectionId,
      activeTab.sessionId,
    ]),
    tabId: activeTab.tabId,
    sessionId: activeTab.sessionId,
  };
}

export function sessionsPanelSelectionReducer(
  state: SessionsPanelSelectionState,
  action: SessionsPanelSelectionAction,
): SessionsPanelSelectionState {
  if (action.type === 'manualSelect') {
    return {
      ...state,
      selection: {
        sessionId: action.sessionId,
        source: 'manual',
      },
      pending: null,
    };
  }

  if (action.type === 'applyPending') {
    if (
      !state.pending ||
      state.pending.intentKey !== action.intentKey ||
      state.followIntentKey !== action.intentKey
    ) {
      return state;
    }
    if (action.nowMs - state.pending.armedAtMs > AUTOSELECT_TTL_MS) {
      return {
        ...state,
        pending: null,
      };
    }
    return {
      ...state,
      selection: {
        sessionId: state.pending.sessionId,
        source: 'activeTab',
        tabId: state.pending.tabId,
      },
      pending: null,
    };
  }

  const connectionChanged = state.connectionId !== action.connectionId;
  const contextChanged =
    connectionChanged ||
    state.enabled !== action.enabled ||
    !activeTabsEqual(state.activeTab, action.activeTab);
  if (!contextChanged) {
    return state;
  }

  const followIntent = resolveFollowIntent(
    action.connectionId,
    action.activeTab,
    action.enabled,
  );
  const followIntentChanged =
    state.followIntentKey !== (followIntent?.key ?? null);

  let selection = connectionChanged ? null : state.selection;
  if (
    selection?.source === 'activeTab' &&
    (!followIntent || followIntentChanged)
  ) {
    selection = null;
  }

  return {
    connectionId: action.connectionId,
    activeTab: action.activeTab,
    enabled: action.enabled,
    followIntentKey: followIntent?.key ?? null,
    selection,
    pending: followIntentChanged
      ? followIntent
        ? {
            intentKey: followIntent.key,
            tabId: followIntent.tabId,
            sessionId: followIntent.sessionId,
            armedAtMs: action.nowMs,
          }
        : null
      : state.pending,
  };
}

export function useSessionsPanelTabAutoSelect(params: {
  connectionId: string | null;
  visibleSessionIds: readonly string[];
  activeTab: ActiveTabSelection;
  enabled: boolean;
}): {
  selectedSessionId: string | null;
  onUserSelectSessionId: (sessionId: string) => void;
  scrollViewRef: RefObject<any>;
  getRowLayoutHandler: (
    sessionId: string,
  ) => (event: LayoutChangeEvent) => void;
  rowLayoutsRef: React.MutableRefObject<
    Record<string, { y: number; height: number }>
  >;
} {
  const { connectionId, visibleSessionIds, activeTab, enabled } = params;

  const [selectionState, dispatchSelection] = useReducer(
    sessionsPanelSelectionReducer,
    INITIAL_SESSIONS_PANEL_SELECTION_STATE,
  );
  const [layoutVersion, setLayoutVersion] = useState(0);

  const scrollViewRef = useRef<any>(null);
  const rowLayoutsRef = useRef<Record<string, { y: number; height: number }>>(
    {},
  );

  const visibleSet = useMemo(
    () => new Set(visibleSessionIds),
    [visibleSessionIds],
  );

  const ensureRowFullyVisible = useCallback(async (sessionId: string) => {
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
    const visibleBottom =
      metrics.offsetY + viewportHeight - VISIBILITY_MARGIN_BOTTOM_PX;

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
  }, []);

  const onUserSelectSessionId = useCallback(
    (sessionId: string) => {
      dispatchSelection({ type: 'manualSelect', sessionId });
      ensureRowFullyVisible(sessionId).catch(() => {});
    },
    [ensureRowFullyVisible],
  );

  useEffect(() => {
    dispatchSelection({
      type: 'reconcile',
      connectionId,
      activeTab: {
        tabId: activeTab.tabId,
        connectionId: activeTab.connectionId,
        sessionId: activeTab.sessionId,
      },
      enabled,
      nowMs: Date.now(),
    });
  }, [
    activeTab.connectionId,
    activeTab.sessionId,
    activeTab.tabId,
    connectionId,
    enabled,
  ]);

  useEffect(() => {
    const pending = selectionState.pending;
    if (
      !pending ||
      !visibleSet.has(pending.sessionId) ||
      !rowLayoutsRef.current[pending.sessionId]
    ) {
      return;
    }

    const nowMs = Date.now();
    dispatchSelection({
      type: 'applyPending',
      intentKey: pending.intentKey,
      nowMs,
    });
    if (nowMs - pending.armedAtMs <= AUTOSELECT_TTL_MS) {
      ensureRowFullyVisible(pending.sessionId).catch(() => {});
    }
  }, [
    ensureRowFullyVisible,
    layoutVersion,
    selectionState.pending,
    visibleSet,
  ]);

  const getRowLayoutHandler = useCallback((sessionId: string) => {
    return (event: LayoutChangeEvent) => {
      const y = Number(event.nativeEvent?.layout?.y ?? NaN);
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (!Number.isFinite(y) || !Number.isFinite(height)) {
        return;
      }
      rowLayoutsRef.current[sessionId] = { y, height };
      setLayoutVersion(prev => prev + 1);
    };
  }, []);

  return {
    selectedSessionId: selectionState.selection?.sessionId ?? null,
    onUserSelectSessionId,
    scrollViewRef,
    getRowLayoutHandler,
    rowLayoutsRef,
  };
}
