import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type RefObject,
} from 'react';
import type {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from 'react-native';

import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import {
  createChatMessageViewportScrollAnchor,
  createChatScrollAnchor,
  isChatMessageViewportScrollAnchor,
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatMessageViewportScrollAnchor,
  type ChatScrollAnchor,
} from './chatScroll';
import {
  createChatScrollCoordinatorState,
  evaluateChatScrollOperationBudget,
  observeChatScrollEdge,
  reduceChatScrollCoordinator,
  type ChatScrollBottomAffinity,
  type ChatScrollCoordinatorEffect,
  type ChatScrollCoordinatorEvent,
  type ChatScrollCoordinatorState,
  type ChatScrollEdge,
  type ChatScrollOperation,
} from './chatScrollCoordinator';
import {
  classifyChatScrollAwayMotion,
  classifyChatScrollReturnToBottom,
  refreshChatScrollMotionGeometry,
  shouldDetachForChatScrollAwayMotion,
  shouldReattachForChatScrollReturnToBottom,
  type ChatScrollMotionSample,
  type ChatScrollProgrammaticWrite,
} from './chatScrollMotionDiagnostics';

type UpdateMessagesCache = (params: {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  scrollAnchor?: unknown;
}) => void;

export type ScrollPersistenceDiagnosticEvent = {
  event: string;
  reason?: string;
  details?: Record<string, unknown>;
};

/**
 * Runtime state for one serialized native edge reconciliation.
 *
 * Coordinator operation IDs are also cancellation generations: every native
 * result is checked against the current ID before it may write a scroll
 * offset. Content-size feedback only marks this operation dirty; it does not
 * create another concurrent native request.
 */
type RuntimeEdgeOperation = {
  operationId: number;
  inFlight: boolean;
  geometryDirty: boolean;
  corrections: number;
  stableSinceMs: number | null;
  stableTargetOffsetY: number | null;
  lastAttemptAtMs: number;
};

const INTERACTION_END_SETTLE_MS = 120;
const DEFAULT_MAX_EDGE_CORRECTIONS = 12;
const RECONCILIATION_POLL_INTERVAL_MS = 16;
const AWAY_MOTION_DIAGNOSTIC_MIN_PX = 2;
const AWAY_MOTION_GEOMETRY_EPSILON_PX = 0.5;
const AWAY_MOTION_GEOMETRY_SETTLE_MS = 100;
const AWAY_MOTION_SEMANTIC_SETTLE_MS = 250;
const AWAY_MOTION_PROGRAMMATIC_WINDOW_MS = 500;
const RETURN_TO_BOTTOM_MIN_TOWARD_PX = 0.5;

function readGlobalBoolean(name: string): boolean {
  const value = (globalThis as any)[name];
  return value === true || value === 'true';
}

function affinityForAnchor(
  anchor: ChatScrollAnchor | ChatMessageViewportScrollAnchor | null,
): ChatScrollBottomAffinity {
  return !anchor || anchor.pinnedToBottom ? 'pinned' : 'detached';
}

function scrollToOffsetY(target: any, offsetY: number) {
  if (!target) {
    return;
  }
  const resolved = Math.max(0, Math.round(offsetY));
  if (typeof target.scrollToOffset === 'function') {
    target.scrollToOffset({ offset: resolved, animated: false });
    return;
  }
  if (typeof target.scrollTo === 'function') {
    target.scrollTo({ y: resolved, animated: false });
    return;
  }
  if (typeof target.scrollToEnd === 'function') {
    target.scrollToEnd({ animated: false });
  }
}

function readScrollMetricsFromEvent(event: NativeSyntheticEvent<NativeScrollEvent>): {
  offsetY: number | null;
  contentHeight: number | null;
  viewportHeight: number | null;
} {
  const nativeEvent = event.nativeEvent;
  const offsetY = Number(nativeEvent?.contentOffset?.y ?? NaN);
  const contentHeight = Number(nativeEvent?.contentSize?.height ?? NaN);
  const viewportHeight = Number(nativeEvent?.layoutMeasurement?.height ?? NaN);
  return {
    offsetY: Number.isFinite(offsetY) ? offsetY : null,
    contentHeight: Number.isFinite(contentHeight) ? contentHeight : null,
    viewportHeight: Number.isFinite(viewportHeight) ? viewportHeight : null,
  };
}

export function useProactiveChatScrollPersistence(params: {
  connectionId: string;
  sessionId: string;
  cachedScrollAnchor: unknown;
  getMessagesForCache: () => IndexedMessage[];
  onUpdateCache: UpdateMessagesCache;
  enabled?: boolean;
  restoreReady?: boolean;
  persistDebounceMs?: number;
  persistThrottleMs?: number;
  bottomThresholdPx?: number;
  bottomConvergenceStableMs?: number;
  bottomConvergenceMaxMs?: number;
  contentFollowLeaseMs?: number;
  manualBottomConvergenceMaxMs?: number;
  initialBottomConvergenceMaxMs?: number;
  contentFollowEnabled?: boolean;
  bottomContentRevision?: unknown;
  maxEdgeCorrections?: number;
  messageAnchorBeforeCount?: number;
  messageAnchorAfterCount?: number;
  messageViewportAnchorsEnabled?: boolean;
  listEdgeMethodsEnabled?: boolean;
  diagnosticsEnabled?: boolean;
  diagnosticsVerbose?: boolean;
  onDiagnosticEvent?: (event: ScrollPersistenceDiagnosticEvent) => void;
  /** @deprecated Use contentFollowLeaseMs. */
  bottomFollowWindowMs?: number;
  /** @deprecated Use manualBottomConvergenceMaxMs. */
  manualBottomFollowWindowMs?: number;
  /** @deprecated Use initialBottomConvergenceMaxMs. */
  initialBottomFollowWindowMs?: number;
  /** @deprecated Use contentFollowEnabled. */
  bottomLockEnabled?: boolean;
}): {
  listRef: RefObject<any>;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollBeginDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollBegin: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onLayout: (event: LayoutChangeEvent) => void;
  onContentSizeChange: (width: number, height: number) => void;
  requestPersist: (reason: string, options?: { force?: boolean; immediate?: boolean }) => void;
  resetRestore: (reason: string) => void;
  scrollToTop: (animated?: boolean) => void;
  scrollToBottom: (animated?: boolean) => void;
  notifyBottomContentChange: (
    reason: string,
    revision: unknown,
    options?: { leaseMs?: number },
  ) => void;
  onListScrollDiagnostic: (event: {
    event: string;
    reason?: string;
    details?: Record<string, unknown>;
  }) => void;
  canScrollToTop: boolean;
  canScrollToBottom: boolean;
  isNearBottom: boolean;
} {
  const {
    connectionId,
    sessionId,
    cachedScrollAnchor,
    getMessagesForCache,
    onUpdateCache,
    enabled = true,
    restoreReady = true,
    persistDebounceMs = 250,
    persistThrottleMs = 1000,
    bottomThresholdPx = PINNED_TO_BOTTOM_THRESHOLD_PX,
    bottomConvergenceStableMs = 200,
    bottomConvergenceMaxMs = 3000,
    contentFollowLeaseMs: configuredContentFollowLeaseMs,
    manualBottomConvergenceMaxMs: configuredManualBottomConvergenceMaxMs,
    initialBottomConvergenceMaxMs: configuredInitialBottomConvergenceMaxMs,
    contentFollowEnabled: configuredContentFollowEnabled,
    bottomContentRevision,
    maxEdgeCorrections = DEFAULT_MAX_EDGE_CORRECTIONS,
    messageAnchorBeforeCount = 40,
    messageAnchorAfterCount = 59,
    messageViewportAnchorsEnabled = false,
    listEdgeMethodsEnabled = false,
    diagnosticsEnabled: configuredDiagnosticsEnabled,
    diagnosticsVerbose: configuredDiagnosticsVerbose,
    onDiagnosticEvent,
    bottomFollowWindowMs,
    manualBottomFollowWindowMs,
    initialBottomFollowWindowMs,
    bottomLockEnabled,
  } = params;

  const contentFollowLeaseMs =
    configuredContentFollowLeaseMs ?? bottomFollowWindowMs ?? 1000;
  const manualBottomConvergenceMaxMs =
    configuredManualBottomConvergenceMaxMs ?? manualBottomFollowWindowMs ?? 3000;
  const initialBottomConvergenceMaxMs =
    configuredInitialBottomConvergenceMaxMs ?? initialBottomFollowWindowMs ?? 5000;
  const contentFollowEnabled =
    configuredContentFollowEnabled ?? bottomLockEnabled ?? false;
  const diagnosticsEnabled =
    configuredDiagnosticsEnabled ??
    (readGlobalBoolean('CLC_DEBUG_CHAT_SCROLL_COORDINATOR') ||
      readGlobalBoolean('CLC_DEBUG_FLATLIST_BOTTOM_FOLLOW'));
  const diagnosticsVerbose =
    configuredDiagnosticsVerbose ??
    readGlobalBoolean('CLC_DEBUG_CHAT_SCROLL_COORDINATOR_VERBOSE');

  const initialAnchor = isChatScrollAnchor(cachedScrollAnchor)
    ? cachedScrollAnchor
    : messageViewportAnchorsEnabled && isChatMessageViewportScrollAnchor(cachedScrollAnchor)
      ? cachedScrollAnchor
      : null;

  const listRef = useRef<any>(null);
  const offsetYRef = useRef(0);
  const contentHeightRef = useRef<number | null>(null);
  const layoutHeightRef = useRef<number | null>(null);
  const isNearBottomRef = useRef(true);
  const geometryRevisionRef = useRef(0);
  const lastGeometryChangeAtMsRef = useRef(0);
  const lastSemanticContentChangeAtMsRef = useRef(0);
  const lastObservedNativeMotionSampleRef = useRef<ChatScrollMotionSample | null>(
    null,
  );
  const lastProgrammaticWriteRef = useRef<ChatScrollProgrammaticWrite | null>(
    null,
  );
  const scrollAffordanceStateRef = useRef({
    canScrollToTop: false,
    canScrollToBottom: false,
    isNearBottom: true,
  });
  const [scrollAffordanceState, setScrollAffordanceState] = useState({
    canScrollToTop: false,
    canScrollToBottom: false,
    isNearBottom: true,
  });

  const initialAnchorRef = useRef<ChatScrollAnchor | ChatMessageViewportScrollAnchor | null>(
    initialAnchor,
  );
  const hasRestoredRef = useRef(false);
  const wasEnabledRef = useRef(enabled);
  const lastBottomContentRevisionRef = useRef(bottomContentRevision);

  const coordinatorRef = useRef<ChatScrollCoordinatorState>(
    createChatScrollCoordinatorState({
      bottomAffinity: affinityForAnchor(initialAnchor),
      initialSemanticRevision: bottomContentRevision,
    }),
  );
  const runtimeOperationRef = useRef<RuntimeEdgeOperation | null>(null);
  const pendingOperationFrameRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const pendingOperationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const runRuntimeOperationRef = useRef<(operationId: number) => void>(() => {});
  const scheduleRuntimeOperationRef = useRef<(operationId: number) => void>(() => {});
  const dispatchCoordinatorRef = useRef<(event: ChatScrollCoordinatorEvent) => void>(() => {});
  const interactionEndTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const followLeaseExpiryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const userInteractionActiveRef = useRef(false);
  const cancelRuntimeOperationOnUnmountRef = useRef<(operationId: number, reason: string) => void>(
    () => {},
  );
  const persistNowOnUnmountRef = useRef<
    (reason: string, options?: { force?: boolean }) => Promise<void>
  >(async () => {});

  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastPersistAtRef = useRef(0);
  const pendingPersistReasonRef = useRef<string | null>(null);
  const lastConsoleDiagnosticAtRef = useRef<Record<string, number>>({});
  const didEmitConfigurationRef = useRef(false);

  const emitDiagnostic = useCallback(
    (event: string, reason?: string, details?: Record<string, unknown>) => {
      const entry = { event, reason, details };
      onDiagnosticEvent?.(entry);

      if (!diagnosticsEnabled) {
        return;
      }
      const verboseOnly =
        event === 'operationCorrection' ||
        event === 'operationObservation' ||
        event === 'geometryChanged' ||
        event === 'followLeaseSkipped' ||
        event === 'awayMotionIgnored' ||
        event === 'manualBottomReattachIgnored';
      if (verboseOnly && !diagnosticsVerbose) {
        return;
      }
      const rateLimitMs =
        event === 'followLeaseRenewed'
          ? 1000
          : event === 'persistSkipped'
            ? 1000
            : event === 'awayMotionCandidate'
              ? 250
              : event === 'manualBottomReattachCandidate'
                ? 250
          : event === 'operationObservation' ||
              event === 'geometryChanged' ||
              event === 'followLeaseSkipped' ||
              event === 'awayMotionIgnored' ||
              event === 'manualBottomReattachIgnored'
            ? 500
            : 0;
      const now = Date.now();
      const previous = lastConsoleDiagnosticAtRef.current[event] ?? 0;
      if (rateLimitMs > 0 && now - previous < rateLimitMs) {
        return;
      }
      lastConsoleDiagnosticAtRef.current[event] = now;
      const payload = {
        connectionId,
        sessionId,
        event,
        reason: reason ?? null,
        ...(details ?? {}),
      };
      console.log('[chatScrollCoordinator]', JSON.stringify(payload));
    },
    [
      connectionId,
      diagnosticsEnabled,
      diagnosticsVerbose,
      onDiagnosticEvent,
      sessionId,
    ],
  );

  useEffect(() => {
    if (didEmitConfigurationRef.current) {
      return;
    }
    didEmitConfigurationRef.current = true;
    emitDiagnostic('configuration', 'effectiveValues', {
      bottomThresholdPx,
      bottomConvergenceStableMs,
      bottomConvergenceMaxMs,
      manualBottomConvergenceMaxMs,
      initialBottomConvergenceMaxMs,
      contentFollowLeaseMs,
      contentFollowEnabled,
      maxEdgeCorrections,
      messageViewportAnchorsEnabled,
      listEdgeMethodsEnabled,
      diagnosticsVerbose,
      awayMotionDiagnosticMinPx: AWAY_MOTION_DIAGNOSTIC_MIN_PX,
      awayMotionGeometrySettleMs: AWAY_MOTION_GEOMETRY_SETTLE_MS,
      awayMotionSemanticSettleMs: AWAY_MOTION_SEMANTIC_SETTLE_MS,
      awayMotionProgrammaticWindowMs:
        AWAY_MOTION_PROGRAMMATIC_WINDOW_MS,
    });
  }, [
    bottomConvergenceMaxMs,
    bottomConvergenceStableMs,
    bottomThresholdPx,
    contentFollowEnabled,
    contentFollowLeaseMs,
    diagnosticsVerbose,
    emitDiagnostic,
    initialBottomConvergenceMaxMs,
    listEdgeMethodsEnabled,
    manualBottomConvergenceMaxMs,
    maxEdgeCorrections,
    messageViewportAnchorsEnabled,
  ]);

  const onListScrollDiagnostic = useCallback(
    (event: {
      event: string;
      reason?: string;
      details?: Record<string, unknown>;
    }) => {
      emitDiagnostic(event.event, event.reason, event.details);
    },
    [emitDiagnostic],
  );

  const updateDerivedScrollState = useCallback(() => {
    const contentHeight = contentHeightRef.current;
    const layoutHeight = layoutHeightRef.current;
    const maxOffsetY =
      contentHeight != null && layoutHeight != null
        ? Math.max(0, contentHeight - layoutHeight)
        : 0;
    const bottomGapPx = Math.max(0, maxOffsetY - offsetYRef.current);
    const topGapPx = Math.max(0, offsetYRef.current);
    const threshold = Math.max(0, bottomThresholdPx);
    const isNearBottom = bottomGapPx <= threshold;
    isNearBottomRef.current = isNearBottom;

    const next = {
      canScrollToTop: topGapPx > threshold,
      canScrollToBottom: bottomGapPx > threshold,
      isNearBottom,
    };
    const current = scrollAffordanceStateRef.current;
    if (
      current.canScrollToTop === next.canScrollToTop &&
      current.canScrollToBottom === next.canScrollToBottom &&
      current.isNearBottom === next.isNearBottom
    ) {
      return;
    }
    scrollAffordanceStateRef.current = next;
    setScrollAffordanceState(next);
  }, [bottomThresholdPx]);

  const applyEventMetrics = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const metrics = readScrollMetricsFromEvent(event);
      if (metrics.offsetY != null) {
        offsetYRef.current = metrics.offsetY;
      }
      if (metrics.contentHeight != null) {
        contentHeightRef.current = metrics.contentHeight;
      }
      if (metrics.viewportHeight != null) {
        layoutHeightRef.current = metrics.viewportHeight;
      }
      updateDerivedScrollState();
    },
    [updateDerivedScrollState],
  );

  const observeNativeMotionForDiagnostics = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>, eventSource: string) => {
      const metrics = readScrollMetricsFromEvent(event);
      if (
        metrics.offsetY == null ||
        metrics.contentHeight == null ||
        metrics.viewportHeight == null
      ) {
        return;
      }
      const now = Date.now();
      const previous = lastObservedNativeMotionSampleRef.current;
      if (
        previous &&
        (Math.abs(previous.contentHeight - metrics.contentHeight) >
          AWAY_MOTION_GEOMETRY_EPSILON_PX ||
          Math.abs(previous.viewportHeight - metrics.viewportHeight) >
            AWAY_MOTION_GEOMETRY_EPSILON_PX)
      ) {
        geometryRevisionRef.current += 1;
        lastGeometryChangeAtMsRef.current = now;
      }
      const current: ChatScrollMotionSample = {
        atMs: now,
        offsetY: metrics.offsetY,
        contentHeight: metrics.contentHeight,
        viewportHeight: metrics.viewportHeight,
        geometryRevision: geometryRevisionRef.current,
      };
      lastObservedNativeMotionSampleRef.current = current;
      if (!previous) {
        return;
      }
      if (
        coordinatorRef.current.bottomAffinity === 'manuallyDetached'
      ) {
        const diagnostic = classifyChatScrollReturnToBottom({
          previous,
          current,
          bottomThresholdPx,
          minTowardMovementPx: RETURN_TO_BOTTOM_MIN_TOWARD_PX,
          geometryEpsilonPx: AWAY_MOTION_GEOMETRY_EPSILON_PX,
          lastGeometryChangeAtMs: lastGeometryChangeAtMsRef.current,
          geometrySettleMs: AWAY_MOTION_GEOMETRY_SETTLE_MS,
          lastSemanticContentChangeAtMs:
            lastSemanticContentChangeAtMsRef.current,
          recentProgrammaticWrite: lastProgrammaticWriteRef.current,
          programmaticWriteWindowMs:
            AWAY_MOTION_PROGRAMMATIC_WINDOW_MS,
        });
        if (!diagnostic) {
          return;
        }
        const operation = coordinatorRef.current.operation;
        emitDiagnostic(
          diagnostic.kind === 'candidate'
            ? 'manualBottomReattachCandidate'
            : 'manualBottomReattachIgnored',
          diagnostic.reason,
          {
            eventSource,
            interaction: coordinatorRef.current.interaction,
            activeOperationId: operation?.id ?? null,
            activeOperationPurpose: operation?.purpose ?? null,
            activeOperationEdge: operation?.edge ?? null,
            ...diagnostic.details,
          },
        );
        if (
          operation != null ||
          !shouldReattachForChatScrollReturnToBottom(diagnostic)
        ) {
          return;
        }
        dispatchCoordinatorRef.current({
          type: 'manualReturnToBottomDetected',
          reason: diagnostic.reason,
          nowMs: now,
          deltaTowardBottomPx: Number(
            diagnostic.details.deltaTowardBottomPx ?? 0,
          ),
          deltaOffsetY: Number(diagnostic.details.deltaOffsetY ?? 0),
        });
        return;
      }
      if (coordinatorRef.current.bottomAffinity !== 'pinned') {
        return;
      }

      const diagnostic = classifyChatScrollAwayMotion({
        previous,
        current,
        minAwayMovementPx: AWAY_MOTION_DIAGNOSTIC_MIN_PX,
        geometryEpsilonPx: AWAY_MOTION_GEOMETRY_EPSILON_PX,
        lastGeometryChangeAtMs: lastGeometryChangeAtMsRef.current,
        geometrySettleMs: AWAY_MOTION_GEOMETRY_SETTLE_MS,
        lastSemanticContentChangeAtMs:
          lastSemanticContentChangeAtMsRef.current,
        semanticContentSettleMs: AWAY_MOTION_SEMANTIC_SETTLE_MS,
        recentProgrammaticWrite: lastProgrammaticWriteRef.current,
        programmaticWriteWindowMs: AWAY_MOTION_PROGRAMMATIC_WINDOW_MS,
      });
      if (!diagnostic) {
        return;
      }
      const operation = coordinatorRef.current.operation;
      emitDiagnostic(
        diagnostic.kind === 'candidate'
          ? 'awayMotionCandidate'
          : 'awayMotionIgnored',
        diagnostic.reason,
        {
          eventSource,
          bottomAffinity: coordinatorRef.current.bottomAffinity,
          interaction: coordinatorRef.current.interaction,
          followLeaseActive:
            coordinatorRef.current.followLease != null &&
            now <= coordinatorRef.current.followLease.expiresAtMs,
          activeOperationId: operation?.id ?? null,
          activeOperationPurpose: operation?.purpose ?? null,
          activeOperationEdge: operation?.edge ?? null,
          ...diagnostic.details,
        },
      );
      if (diagnostic.kind !== 'candidate') {
        return;
      }
      const recentProgrammaticWrite =
        diagnostic.details.recentProgrammaticWrite === true;
      const movementOpposesProgrammaticTarget =
        diagnostic.details.movementOpposesProgrammaticTarget === true;
      if (!shouldDetachForChatScrollAwayMotion(diagnostic)) {
        emitDiagnostic(
          'awayMotionDetachSuppressed',
          'recentProgrammaticMovementNotOpposed',
          {
            eventSource,
            ...diagnostic.details,
          },
        );
        return;
      }
      dispatchCoordinatorRef.current({
        type: 'manualAwayMotionDetected',
        reason: diagnostic.reason,
        nowMs: now,
        deltaBottomGapPx: Number(
          diagnostic.details.deltaBottomGapPx ?? 0,
        ),
        deltaOffsetY: Number(diagnostic.details.deltaOffsetY ?? 0),
        recentProgrammaticWrite,
        movementOpposesProgrammaticTarget,
      });
    },
    [bottomThresholdPx, emitDiagnostic],
  );

  const markGeometryChangedForMotionDiagnostics = useCallback(
    (previousValue: number | null, nextValue: number) => {
      if (
        previousValue == null ||
        Math.abs(previousValue - nextValue) >
          AWAY_MOTION_GEOMETRY_EPSILON_PX
      ) {
        geometryRevisionRef.current += 1;
        lastGeometryChangeAtMsRef.current = Date.now();
      }
    },
    [],
  );

  const refreshObservedMotionGeometryBaseline = useCallback(() => {
    lastObservedNativeMotionSampleRef.current =
      refreshChatScrollMotionGeometry(
        lastObservedNativeMotionSampleRef.current,
        {
          atMs: Date.now(),
          contentHeight: contentHeightRef.current,
          viewportHeight: layoutHeightRef.current,
          geometryRevision: geometryRevisionRef.current,
        },
      );
  }, []);

  const cancelRuntimeOperation = useCallback(
    (operationId: number, reason: string) => {
      if (runtimeOperationRef.current?.operationId !== operationId) {
        return;
      }
      if (pendingOperationFrameRef.current != null) {
        cancelAnimationFrame(pendingOperationFrameRef.current);
        pendingOperationFrameRef.current = null;
      }
      if (pendingOperationTimerRef.current != null) {
        clearTimeout(pendingOperationTimerRef.current);
        pendingOperationTimerRef.current = null;
      }
      runtimeOperationRef.current = null;
      emitDiagnostic('runtimeOperationCancelled', reason, { operationId });
    },
    [emitDiagnostic],
  );
  cancelRuntimeOperationOnUnmountRef.current = cancelRuntimeOperation;

  const applyCoordinatorEffects = useCallback(
    (effects: ChatScrollCoordinatorEffect[]) => {
      for (const effect of effects) {
        if (effect.type === 'cancelRuntimeOperation') {
          cancelRuntimeOperation(effect.operationId, effect.reason);
        } else {
          scheduleRuntimeOperationRef.current(effect.operationId);
        }
      }
    },
    [cancelRuntimeOperation],
  );

  const dispatchCoordinator = useCallback(
    (event: ChatScrollCoordinatorEvent) => {
      const previousLeaseExpiry = coordinatorRef.current.followLease?.expiresAtMs ?? null;
      const next = reduceChatScrollCoordinator(coordinatorRef.current, event);
      coordinatorRef.current = next.state;
      const nextLeaseExpiry = next.state.followLease?.expiresAtMs ?? null;
      if (previousLeaseExpiry !== nextLeaseExpiry) {
        if (followLeaseExpiryTimerRef.current) {
          clearTimeout(followLeaseExpiryTimerRef.current);
          followLeaseExpiryTimerRef.current = null;
        }
        if (nextLeaseExpiry != null) {
          const delayMs = Math.max(1, nextLeaseExpiry - Date.now() + 1);
          followLeaseExpiryTimerRef.current = setTimeout(() => {
            followLeaseExpiryTimerRef.current = null;
            dispatchCoordinatorRef.current({
              type: 'geometryChanged',
              reason: 'followLeaseDeadline',
              nowMs: Date.now(),
            });
          }, delayMs);
        }
      }
      for (const diagnostic of next.diagnostics) {
        emitDiagnostic(diagnostic.event, diagnostic.reason, diagnostic.details);
      }
      applyCoordinatorEffects(next.effects);
      return next.state;
    },
    [applyCoordinatorEffects, emitDiagnostic],
  );
  dispatchCoordinatorRef.current = dispatchCoordinator;

  const writeEdge = useCallback(
    (
      operation: ChatScrollOperation,
      animated: boolean,
      context: {
        reason: string;
        measuredTargetOffsetY?: number;
        measuredGapPx?: number;
      },
    ) => {
      const target = listRef.current;
      if (!target || coordinatorRef.current.operation?.id !== operation.id) {
        return false;
      }

      const measuredTargetOffsetY = context.measuredTargetOffsetY;
      let targetOffsetY =
        typeof measuredTargetOffsetY === 'number'
          ? measuredTargetOffsetY
          : operation.edge === 'bottom'
            ? Math.max(0, (contentHeightRef.current ?? 0) - (layoutHeightRef.current ?? 0))
            : 0;

      if (
        listEdgeMethodsEnabled &&
        operation.edge === 'top' &&
        typeof target.scrollToTop === 'function'
      ) {
        target.scrollToTop({ animated });
        targetOffsetY = 0;
      } else if (
        listEdgeMethodsEnabled &&
        operation.edge === 'bottom' &&
        typeof target.scrollToBottom === 'function'
      ) {
        target.scrollToBottom({ animated });
      } else if (typeof target.scrollToOffset === 'function') {
        target.scrollToOffset({ offset: targetOffsetY, animated });
      } else if (typeof target.scrollTo === 'function') {
        target.scrollTo({ y: targetOffsetY, animated });
      } else if (operation.edge === 'bottom' && typeof target.scrollToEnd === 'function') {
        target.scrollToEnd({ animated });
      } else {
        return false;
      }

      lastProgrammaticWriteRef.current = {
        atMs: Date.now(),
        operationId: operation.id,
        purpose: operation.purpose,
        edge: operation.edge,
        targetOffsetY,
      };
      offsetYRef.current = targetOffsetY;
      updateDerivedScrollState();
      emitDiagnostic('operationCorrection', context.reason, {
        operationId: operation.id,
        purpose: operation.purpose,
        edge: operation.edge,
        correction:
          operation.purpose === 'contentFollow'
            ? (coordinatorRef.current.followLease?.correctionCount ?? 0) + 1
            : (runtimeOperationRef.current?.corrections ?? 0) + 1,
        targetOffsetY: Math.round(targetOffsetY),
        measuredGapPx:
          typeof context.measuredGapPx === 'number'
            ? Math.round(context.measuredGapPx)
            : null,
      });
      return true;
    },
    [emitDiagnostic, listEdgeMethodsEnabled, updateDerivedScrollState],
  );

  const stopOperation = useCallback(
    (
      operationId: number,
      outcome: 'expired' | 'cancelled' | 'correctionLimit' | 'unavailable',
      reason: string,
    ) => {
      if (
        coordinatorRef.current.operation?.id !== operationId ||
        runtimeOperationRef.current?.operationId !== operationId
      ) {
        return;
      }
      if (pendingOperationFrameRef.current != null) {
        cancelAnimationFrame(pendingOperationFrameRef.current);
        pendingOperationFrameRef.current = null;
      }
      if (pendingOperationTimerRef.current != null) {
        clearTimeout(pendingOperationTimerRef.current);
        pendingOperationTimerRef.current = null;
      }
      if (runtimeOperationRef.current?.operationId === operationId) {
        runtimeOperationRef.current = null;
      }
      dispatchCoordinator({
        type: 'operationStopped',
        operationId,
        outcome,
        reason,
        nowMs: Date.now(),
      });
    },
    [dispatchCoordinator],
  );

  const scheduleRuntimeOperation = useCallback((operationId: number) => {
    const operation = coordinatorRef.current.operation;
    if (!operation || operation.id !== operationId) {
      return;
    }
    let runtime = runtimeOperationRef.current;
    if (!runtime || runtime.operationId !== operationId) {
      runtime = {
        operationId,
        inFlight: false,
        geometryDirty: true,
        corrections: 0,
        stableSinceMs: null,
        stableTargetOffsetY: null,
        lastAttemptAtMs: 0,
      };
      runtimeOperationRef.current = runtime;
    } else {
      runtime.geometryDirty = true;
    }
    if (
      runtime.inFlight ||
      pendingOperationFrameRef.current != null ||
      pendingOperationTimerRef.current != null
    ) {
      return;
    }
    const delayMs = Math.max(
      0,
      runtime.lastAttemptAtMs + RECONCILIATION_POLL_INTERVAL_MS - Date.now(),
    );
    if (delayMs > 0) {
      pendingOperationTimerRef.current = setTimeout(() => {
        pendingOperationTimerRef.current = null;
        scheduleRuntimeOperationRef.current(operationId);
      }, delayMs);
      return;
    }
    pendingOperationFrameRef.current = requestAnimationFrame(() => {
      pendingOperationFrameRef.current = null;
      runRuntimeOperationRef.current(operationId);
    });
  }, []);
  scheduleRuntimeOperationRef.current = scheduleRuntimeOperation;

  runRuntimeOperationRef.current = (operationId: number) => {
    const operation = coordinatorRef.current.operation;
    const runtime = runtimeOperationRef.current;
    if (
      !operation ||
      operation.id !== operationId ||
      !runtime ||
      runtime.operationId !== operationId ||
      coordinatorRef.current.interaction !== 'idle'
    ) {
      return;
    }

    const startedAt = Date.now();
    runtime.lastAttemptAtMs = startedAt;
    if (
      evaluateChatScrollOperationBudget({
        nowMs: startedAt,
        deadlineMs: operation.deadlineMs,
        corrections: 0,
        maxCorrections: maxEdgeCorrections,
      }) === 'expired'
    ) {
      stopOperation(operationId, 'expired', 'deadlineBeforeMetrics');
      return;
    }
    if (runtime.inFlight) {
      runtime.geometryDirty = true;
      return;
    }
    runtime.inFlight = true;
    runtime.geometryDirty = false;

    getMacScrollViewMetrics(listRef.current)
      .then((metrics) => {
        const currentOperation = coordinatorRef.current.operation;
        const currentRuntime = runtimeOperationRef.current;
        if (
          !currentOperation ||
          currentOperation.id !== operationId ||
          !currentRuntime ||
          currentRuntime.operationId !== operationId ||
          coordinatorRef.current.interaction !== 'idle'
        ) {
          return;
        }
        currentRuntime.inFlight = false;
        const geometryChangedWhileInFlight = currentRuntime.geometryDirty;
        currentRuntime.geometryDirty = false;
        if (!metrics) {
          stopOperation(operationId, 'unavailable', 'nativeMetricsUnavailable');
          return;
        }

        offsetYRef.current = metrics.offsetY;
        contentHeightRef.current = metrics.contentHeight;
        layoutHeightRef.current = metrics.viewportHeight;
        updateDerivedScrollState();

        const now = Date.now();
        const budget = evaluateChatScrollOperationBudget({
          nowMs: now,
          deadlineMs: currentOperation.deadlineMs,
          corrections:
            currentOperation.purpose === 'contentFollow'
              ? coordinatorRef.current.followLease?.correctionCount ?? 0
              : currentRuntime.corrections,
          maxCorrections: maxEdgeCorrections,
        });
        if (budget === 'expired') {
          stopOperation(operationId, 'expired', 'deadlineAfterMetrics');
          return;
        }
        if (geometryChangedWhileInFlight) {
          currentRuntime.stableSinceMs = null;
          currentRuntime.stableTargetOffsetY = null;
          scheduleRuntimeOperationRef.current(operationId);
          return;
        }

        const observation = observeChatScrollEdge({
          edge: currentOperation.edge,
          offsetY: metrics.offsetY,
          contentHeight: metrics.contentHeight,
          viewportHeight: metrics.viewportHeight,
          epsilonPx: bottomThresholdPx,
        });
        emitDiagnostic('operationObservation', 'nativeMetrics', {
          operationId,
          purpose: currentOperation.purpose,
          edge: currentOperation.edge,
          edgeGapPx: Math.round(observation.edgeGapPx),
          targetOffsetY: Math.round(observation.targetOffsetY),
          corrections: currentRuntime.corrections,
        });

        if (observation.withinEpsilon) {
          if (
            currentRuntime.stableSinceMs == null ||
            currentRuntime.stableTargetOffsetY == null ||
            Math.abs(currentRuntime.stableTargetOffsetY - observation.targetOffsetY) >
              bottomThresholdPx
          ) {
            currentRuntime.stableSinceMs = now;
            currentRuntime.stableTargetOffsetY = observation.targetOffsetY;
            scheduleRuntimeOperationRef.current(operationId);
            return;
          }
          if (now - currentRuntime.stableSinceMs >= bottomConvergenceStableMs) {
            runtimeOperationRef.current = null;
            dispatchCoordinator({
              type: 'operationCompleted',
              operationId,
              reason: 'stable',
              nowMs: now,
            });
            return;
          }
          scheduleRuntimeOperationRef.current(operationId);
          return;
        }

        currentRuntime.stableSinceMs = null;
        currentRuntime.stableTargetOffsetY = null;
        if (budget === 'correctionLimit') {
          stopOperation(operationId, 'correctionLimit', 'maxCorrections');
          return;
        }

        const wrote = writeEdge(currentOperation, false, {
          reason: 'reconcile',
          measuredTargetOffsetY: observation.targetOffsetY,
          measuredGapPx: observation.edgeGapPx,
        });
        if (!wrote) {
          stopOperation(operationId, 'unavailable', 'missingScrollMethod');
          return;
        }
        if (currentOperation.purpose === 'contentFollow') {
          dispatchCoordinator({
            type: 'operationCorrectionIssued',
            operationId,
            nowMs: now,
          });
        }
        currentRuntime.corrections += 1;
        scheduleRuntimeOperationRef.current(operationId);
      })
      .catch(() => {
        if (runtimeOperationRef.current?.operationId === operationId) {
          runtimeOperationRef.current.inFlight = false;
        }
        stopOperation(operationId, 'unavailable', 'nativeMetricsError');
      });
  };

  const startNavigation = useCallback(
    (options: {
      edge: ChatScrollEdge;
      animated: boolean;
      source: 'manual' | 'initialRestore' | 'anchorRestore';
      reason: string;
      maxDurationMs: number;
    }) => {
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      userInteractionActiveRef.current = false;
      const state = dispatchCoordinator({
        type: 'startNavigation',
        edge: options.edge,
        source: options.source,
        reason: options.reason,
        nowMs: Date.now(),
        maxDurationMs: options.maxDurationMs,
      });
      const operation = state.operation;
      if (!operation) {
        return;
      }
      const runtime = runtimeOperationRef.current;
      if (writeEdge(operation, options.animated, { reason: 'navigationInitial' }) && runtime) {
        runtime.corrections += 1;
      }
      scheduleRuntimeOperationRef.current(operation.id);
    },
    [dispatchCoordinator, writeEdge],
  );

  const scrollToTop = useCallback(
    (animated = true) => {
      startNavigation({
        edge: 'top',
        animated,
        source: 'manual',
        reason: 'scrollToTop',
        maxDurationMs: bottomConvergenceMaxMs,
      });
    },
    [bottomConvergenceMaxMs, startNavigation],
  );

  const scrollToBottom = useCallback(
    (animated = true) => {
      startNavigation({
        edge: 'bottom',
        animated,
        source: 'manual',
        reason: 'scrollToBottom',
        maxDurationMs: manualBottomConvergenceMaxMs,
      });
    },
    [manualBottomConvergenceMaxMs, startNavigation],
  );

  const notifyBottomContentChange = useCallback(
    (reason: string, revision: unknown, options?: { leaseMs?: number }) => {
      lastSemanticContentChangeAtMsRef.current = Date.now();
      dispatchCoordinator({
        type: 'semanticContentChanged',
        revision,
        reason,
        nowMs: Date.now(),
        leaseMs: options?.leaseMs ?? contentFollowLeaseMs,
        followEnabled: contentFollowEnabled && enabled,
        restoreComplete: hasRestoredRef.current,
      });
    },
    [
      contentFollowEnabled,
      contentFollowLeaseMs,
      dispatchCoordinator,
      enabled,
    ],
  );

  useEffect(() => {
    if (Object.is(lastBottomContentRevisionRef.current, bottomContentRevision)) {
      return;
    }
    lastBottomContentRevisionRef.current = bottomContentRevision;
    notifyBottomContentChange('bottomContentChanged', bottomContentRevision);
  }, [bottomContentRevision, notifyBottomContentChange]);

  const maybeRestoreScroll = useCallback(() => {
    if (!enabled || !restoreReady || hasRestoredRef.current) {
      return;
    }
    const contentHeight = contentHeightRef.current;
    const layoutHeight = layoutHeightRef.current;
    if (
      contentHeight == null ||
      layoutHeight == null ||
      !Number.isFinite(contentHeight) ||
      !Number.isFinite(layoutHeight) ||
      layoutHeight <= 0
    ) {
      return;
    }

    const anchor = initialAnchorRef.current;
    if (!anchor || anchor.pinnedToBottom) {
      emitDiagnostic('restoreStarted', !anchor ? 'noAnchorBottom' : 'pinnedBottom', {
        maxDurationMs: initialBottomConvergenceMaxMs,
      });
      hasRestoredRef.current = true;
      startNavigation({
        edge: 'bottom',
        animated: false,
        source: !anchor ? 'initialRestore' : 'anchorRestore',
        reason: !anchor ? 'restoreNoAnchorBottom' : 'restorePinnedBottom',
        maxDurationMs: initialBottomConvergenceMaxMs,
      });
      return;
    }

    const target = listRef.current;
    if (!target) {
      return;
    }

    dispatchCoordinator({
      type: 'setBottomAffinity',
      bottomAffinity: 'detached',
      reason: 'restoreDetachedAnchor',
      nowMs: Date.now(),
    });

    if (
      messageViewportAnchorsEnabled &&
      isChatMessageViewportScrollAnchor(anchor) &&
      typeof target.scrollToItemAnchor === 'function'
    ) {
      emitDiagnostic('restoreStarted', 'messageViewport', { anchor });
      target.scrollToItemAnchor({
        key: `msg-${anchor.messageIndex}`,
        offsetFromViewportTop: anchor.offsetFromViewportTop,
        beforeCount: messageAnchorBeforeCount,
        afterCount: messageAnchorAfterCount,
        animated: false,
      });
      hasRestoredRef.current = true;
      emitDiagnostic('restoreScheduled', 'messageViewport', { anchor });
      return;
    }

    if (isChatScrollAnchor(anchor)) {
      const maxOffsetY = Math.max(0, contentHeight - layoutHeight);
      const targetOffsetY = Math.max(0, maxOffsetY - anchor.bottomGapPx);
      emitDiagnostic('restoreStarted', 'offsetAnchor', { anchor, targetOffsetY });
      scrollToOffsetY(target, targetOffsetY);
      offsetYRef.current = targetOffsetY;
      updateDerivedScrollState();
      hasRestoredRef.current = true;
      emitDiagnostic('restoreCompleted', 'offsetAnchor', { anchor, targetOffsetY });
      return;
    }

    hasRestoredRef.current = true;
    emitDiagnostic('restoreSkipped', 'unsupportedAnchor', { anchor });
  }, [
    dispatchCoordinator,
    emitDiagnostic,
    enabled,
    initialBottomConvergenceMaxMs,
    messageAnchorAfterCount,
    messageAnchorBeforeCount,
    messageViewportAnchorsEnabled,
    restoreReady,
    startNavigation,
    updateDerivedScrollState,
  ]);

  const persistNow = useCallback(
    async (
      reason: string,
      options?: {
        force?: boolean;
      },
    ) => {
      if (!enabled) {
        return;
      }
      const now = Date.now();
      if (!options?.force && now - lastPersistAtRef.current < persistThrottleMs) {
        return;
      }
      lastPersistAtRef.current = now;

      const metrics = await getMacScrollViewMetrics(listRef.current);
      if (!metrics) {
        emitDiagnostic('persistSkipped', 'nativeMetricsUnavailable');
        return;
      }

      const maxOffsetY = Math.max(0, metrics.contentHeight - metrics.viewportHeight);
      const bottomGapPx = Math.max(0, maxOffsetY - metrics.offsetY);
      const pinnedToBottom = bottomGapPx <= bottomThresholdPx;
      let anchor: ChatScrollAnchor | ChatMessageViewportScrollAnchor =
        createChatScrollAnchor({ bottomGapPx, pinnedToBottom });

      if (messageViewportAnchorsEnabled && !pinnedToBottom) {
        const visibleAnchor =
          typeof listRef.current?.getVisibleAnchor === 'function'
            ? await listRef.current.getVisibleAnchor()
            : null;
        const visibleKey =
          typeof visibleAnchor?.key === 'string' ? visibleAnchor.key : null;
        const match = visibleKey ? /^msg-(-?\d+)$/.exec(visibleKey) : null;
        if (match) {
          const messageIndex = Number(match[1]);
          const offsetFromViewportTop = Number(visibleAnchor.offsetFromViewportTop ?? NaN);
          if (Number.isFinite(messageIndex) && Number.isFinite(offsetFromViewportTop)) {
            anchor = createChatMessageViewportScrollAnchor({
              messageIndex,
              offsetFromViewportTop,
              pinnedToBottom: false,
            });
          }
        }
      }

      emitDiagnostic('persistAnchor', reason, {
        anchor,
        metrics: {
          offsetY: Math.round(metrics.offsetY),
          viewportHeight: Math.round(metrics.viewportHeight),
          contentHeight: Math.round(metrics.contentHeight),
        },
      });
      onUpdateCache({
        connectionId,
        sessionId,
        messages: getMessagesForCache(),
        scrollAnchor: anchor,
      });
    },
    [
      bottomThresholdPx,
      connectionId,
      emitDiagnostic,
      enabled,
      getMessagesForCache,
      messageViewportAnchorsEnabled,
      onUpdateCache,
      persistThrottleMs,
      sessionId,
    ],
  );

  const requestPersist = useCallback(
    (reason: string, options?: { force?: boolean; immediate?: boolean }) => {
      if (!enabled) {
        return;
      }
      if (options?.immediate) {
        if (persistTimerRef.current) {
          clearTimeout(persistTimerRef.current);
          persistTimerRef.current = null;
        }
        pendingPersistReasonRef.current = null;
        persistNow(reason, { force: options.force }).catch(() => {});
        return;
      }
      pendingPersistReasonRef.current = reason;
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
      }
      persistTimerRef.current = setTimeout(() => {
        const nextReason = pendingPersistReasonRef.current ?? 'unknown';
        pendingPersistReasonRef.current = null;
        persistTimerRef.current = null;
        persistNow(nextReason, { force: options?.force }).catch(() => {});
      }, persistDebounceMs);
    },
    [enabled, persistDebounceMs, persistNow],
  );
  persistNowOnUnmountRef.current = persistNow;

  const resetRestore = useCallback(
    (reason: string) => {
      dispatchCoordinator({ type: 'clear', reason, nowMs: Date.now() });
      dispatchCoordinator({
        type: 'setBottomAffinity',
        bottomAffinity: affinityForAnchor(initialAnchorRef.current),
        reason: `${reason}:anchorAffinity`,
        nowMs: Date.now(),
      });
      hasRestoredRef.current = false;
      maybeRestoreScroll();
    },
    [dispatchCoordinator, maybeRestoreScroll],
  );

  useEffect(() => {
    initialAnchorRef.current = isChatScrollAnchor(cachedScrollAnchor)
      ? cachedScrollAnchor
      : messageViewportAnchorsEnabled && isChatMessageViewportScrollAnchor(cachedScrollAnchor)
        ? cachedScrollAnchor
        : null;
    maybeRestoreScroll();
  }, [cachedScrollAnchor, maybeRestoreScroll, messageViewportAnchorsEnabled]);

  useEffect(() => {
    const wasEnabled = wasEnabledRef.current;
    wasEnabledRef.current = enabled;
    if (!wasEnabled && enabled) {
      resetRestore('becameEnabled');
    }
    if (wasEnabled && !enabled) {
      dispatchCoordinator({ type: 'clear', reason: 'becameDisabled', nowMs: Date.now() });
    }
  }, [dispatchCoordinator, enabled, resetRestore]);

  useEffect(() => {
    return () => {
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
        persistTimerRef.current = null;
      }
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      if (followLeaseExpiryTimerRef.current) {
        clearTimeout(followLeaseExpiryTimerRef.current);
        followLeaseExpiryTimerRef.current = null;
      }
      const operationId = coordinatorRef.current.operation?.id;
      if (operationId != null) {
        cancelRuntimeOperationOnUnmountRef.current(operationId, 'unmount');
      }
      persistNowOnUnmountRef.current('unmount', { force: true }).catch(() => {});
    };
  }, []);

  const signalGeometryChanged = useCallback(
    (reason: string) => {
      emitDiagnostic('geometryChanged', reason, {
        contentHeight:
          contentHeightRef.current == null ? null : Math.round(contentHeightRef.current),
        viewportHeight:
          layoutHeightRef.current == null ? null : Math.round(layoutHeightRef.current),
      });
      dispatchCoordinator({ type: 'geometryChanged', reason, nowMs: Date.now() });
    },
    [dispatchCoordinator, emitDiagnostic],
  );

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (Number.isFinite(height)) {
        markGeometryChangedForMotionDiagnostics(
          layoutHeightRef.current,
          height,
        );
        layoutHeightRef.current = height;
        refreshObservedMotionGeometryBaseline();
      }
      updateDerivedScrollState();
      maybeRestoreScroll();
      signalGeometryChanged('layout');
    },
    [
      markGeometryChangedForMotionDiagnostics,
      maybeRestoreScroll,
      refreshObservedMotionGeometryBaseline,
      signalGeometryChanged,
      updateDerivedScrollState,
    ],
  );

  const onContentSizeChange = useCallback(
    (_width: number, height: number) => {
      const resolved = Number(height ?? NaN);
      if (Number.isFinite(resolved)) {
        markGeometryChangedForMotionDiagnostics(
          contentHeightRef.current,
          resolved,
        );
        contentHeightRef.current = resolved;
        refreshObservedMotionGeometryBaseline();
      }
      updateDerivedScrollState();
      maybeRestoreScroll();
      signalGeometryChanged('contentSizeChange');
    },
    [
      markGeometryChangedForMotionDiagnostics,
      maybeRestoreScroll,
      refreshObservedMotionGeometryBaseline,
      signalGeometryChanged,
      updateDerivedScrollState,
    ],
  );

  const onScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      observeNativeMotionForDiagnostics(event, 'scroll');
      applyEventMetrics(event);
      const operationId = coordinatorRef.current.operation?.id;
      if (operationId != null) {
        scheduleRuntimeOperationRef.current(operationId);
      }
    },
    [applyEventMetrics, observeNativeMotionForDiagnostics],
  );

  const beginInteraction = useCallback(
    (
      interaction: 'dragging' | 'momentum',
      reason: string,
      event: NativeSyntheticEvent<NativeScrollEvent>,
    ) => {
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      userInteractionActiveRef.current = true;
      observeNativeMotionForDiagnostics(event, reason);
      applyEventMetrics(event);
      dispatchCoordinator({
        type: 'interactionBegan',
        interaction,
        reason,
        nowMs: Date.now(),
      });
    },
    [
      applyEventMetrics,
      dispatchCoordinator,
      observeNativeMotionForDiagnostics,
    ],
  );

  const finishInteraction = useCallback(
    (reason: string, event?: NativeSyntheticEvent<NativeScrollEvent>) => {
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      if (event) {
        observeNativeMotionForDiagnostics(event, reason);
        applyEventMetrics(event);
      }
      userInteractionActiveRef.current = false;
      dispatchCoordinator({
        type: 'interactionEnded',
        atBottom: isNearBottomRef.current,
        reason,
        nowMs: Date.now(),
      });
    },
    [
      applyEventMetrics,
      dispatchCoordinator,
      observeNativeMotionForDiagnostics,
    ],
  );

  const onScrollBeginDrag = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      beginInteraction('dragging', 'scrollBeginDrag', event);
    },
    [beginInteraction],
  );

  const onScrollEndDrag = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      applyEventMetrics(event);
      requestPersist('scrollEndDrag');
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
      }
      interactionEndTimerRef.current = setTimeout(() => {
        interactionEndTimerRef.current = null;
        finishInteraction('scrollEndDragSettled');
      }, INTERACTION_END_SETTLE_MS);
    },
    [applyEventMetrics, finishInteraction, requestPersist],
  );

  const onMomentumScrollBegin = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      if (userInteractionActiveRef.current) {
        beginInteraction('momentum', 'momentumScrollBegin', event);
        return;
      }
      // Some RN list implementations emit momentum callbacks for animated
      // programmatic navigation. Without a preceding drag this is observation,
      // not user intent, and must not cancel the navigation operation.
      observeNativeMotionForDiagnostics(event, 'programmaticMomentumBegin');
      applyEventMetrics(event);
      const operationId = coordinatorRef.current.operation?.id;
      if (operationId != null) {
        scheduleRuntimeOperationRef.current(operationId);
      }
    },
    [applyEventMetrics, beginInteraction, observeNativeMotionForDiagnostics],
  );

  const onMomentumScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      if (userInteractionActiveRef.current) {
        finishInteraction('momentumScrollEnd', event);
        requestPersist('scrollMomentumEnd');
      } else {
        observeNativeMotionForDiagnostics(event, 'programmaticMomentumEnd');
        applyEventMetrics(event);
        const operationId = coordinatorRef.current.operation?.id;
        if (operationId != null) {
          scheduleRuntimeOperationRef.current(operationId);
          emitDiagnostic('persistSkipped', 'programmaticMomentumDuringOperation', {
            operationId,
          });
        } else {
          requestPersist('programmaticMomentumEnd');
        }
      }
    },
    [
      applyEventMetrics,
      emitDiagnostic,
      finishInteraction,
      observeNativeMotionForDiagnostics,
      requestPersist,
    ],
  );

  const result = useMemo(
    () => ({
      listRef,
      onScroll,
      onScrollBeginDrag,
      onScrollEndDrag,
      onMomentumScrollBegin,
      onMomentumScrollEnd,
      onLayout,
      onContentSizeChange,
      requestPersist,
      resetRestore,
      scrollToTop,
      scrollToBottom,
      notifyBottomContentChange,
      onListScrollDiagnostic,
      canScrollToTop: scrollAffordanceState.canScrollToTop,
      canScrollToBottom: scrollAffordanceState.canScrollToBottom,
      isNearBottom: scrollAffordanceState.isNearBottom,
    }),
    [
      notifyBottomContentChange,
      onListScrollDiagnostic,
      onContentSizeChange,
      onLayout,
      onMomentumScrollBegin,
      onMomentumScrollEnd,
      onScroll,
      onScrollBeginDrag,
      onScrollEndDrag,
      requestPersist,
      resetRestore,
      scrollAffordanceState.canScrollToBottom,
      scrollAffordanceState.canScrollToTop,
      scrollAffordanceState.isNearBottom,
      scrollToBottom,
      scrollToTop,
    ],
  );

  return result;
}
