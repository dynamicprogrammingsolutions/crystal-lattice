import type { AgentBackend } from '../backend/backend';
import type { RefreshUiEffects } from '../types/plugins';
import type { Unsubscribe } from '../util/subscribable';
import { emitApplicationActionsInvalidated } from './applicationActionsInvalidation';

export type RefreshUiEffect =
  | { type: 'reloadSession'; sessionId: string }
  | { type: 'reloadSessionsList' }
  | { type: 'reloadApplicationActions' };

export type RefreshUiInvalidation = RefreshUiEffect & {
  invalidationRevision: number;
};

type Listener = (effect: RefreshUiInvalidation) => void;

interface BackendInvalidationState {
  nextRevision: number;
  pendingSessionRevisions: Map<string, number>;
  pendingSessionsListRevision: number | null;
  claimedSessionRevisions: Map<string, number>;
  claimedSessionsListRevision: number | null;
  listeners: Set<Listener>;
}

const STATE_BY_BACKEND: WeakMap<object, BackendInvalidationState> = new WeakMap();

function getState(backend: AgentBackend): BackendInvalidationState {
  let state = STATE_BY_BACKEND.get(backend as object);
  if (!state) {
    state = {
      nextRevision: 0,
      pendingSessionRevisions: new Map(),
      pendingSessionsListRevision: null,
      claimedSessionRevisions: new Map(),
      claimedSessionsListRevision: null,
      listeners: new Set(),
    };
    STATE_BY_BACKEND.set(backend as object, state);
  }
  return state;
}

function pendingInvalidations(state: BackendInvalidationState): RefreshUiInvalidation[] {
  return [
    ...[...state.pendingSessionRevisions.entries()].map(
      ([sessionId, invalidationRevision]) => ({
        type: 'reloadSession' as const,
        sessionId,
        invalidationRevision,
      }),
    ),
    ...(state.pendingSessionsListRevision == null
      ? []
      : [
          {
            type: 'reloadSessionsList' as const,
            invalidationRevision: state.pendingSessionsListRevision,
          },
        ]),
  ];
}

export function parseRefreshUiEffects(value: unknown): RefreshUiEffect[] {
  if (!value || typeof value !== 'object') return [];
  const raw = value as RefreshUiEffects;
  const effects: RefreshUiEffect[] = [];
  const seen = new Set<string>();
  if (Array.isArray(raw.reload_session_ids)) {
    for (const sessionId of raw.reload_session_ids) {
      if (typeof sessionId !== 'string' || !sessionId || seen.has(sessionId)) continue;
      seen.add(sessionId);
      effects.push({ type: 'reloadSession', sessionId });
    }
  }
  if (raw.reload_sessions_list === true) effects.push({ type: 'reloadSessionsList' });
  if (raw.reload_application_actions === true) {
    effects.push({ type: 'reloadApplicationActions' });
  }
  return effects;
}

export function subscribeRefreshUiEffects(backend: AgentBackend, listener: Listener): Unsubscribe {
  const state = getState(backend);
  state.listeners.add(listener);
  for (const effect of pendingInvalidations(state)) {
    listener(effect);
  }
  return () => state.listeners.delete(listener);
}

export function acknowledgeRefreshUiEffect(
  backend: AgentBackend,
  effect: RefreshUiInvalidation,
): void {
  const state = getState(backend);
  if (effect.type === 'reloadSession') {
    if (
      state.pendingSessionRevisions.get(effect.sessionId) ===
      effect.invalidationRevision
    ) {
      state.pendingSessionRevisions.delete(effect.sessionId);
      state.claimedSessionRevisions.delete(effect.sessionId);
    }
    return;
  }
  if (
    effect.type === 'reloadSessionsList' &&
    state.pendingSessionsListRevision === effect.invalidationRevision
  ) {
    state.pendingSessionsListRevision = null;
    state.claimedSessionsListRevision = null;
  }
}

function claimRefreshUiEffect(
  state: BackendInvalidationState,
  effect: RefreshUiInvalidation,
): boolean {
  if (effect.type === 'reloadSession') {
    if (
      state.claimedSessionRevisions.get(effect.sessionId) ===
      effect.invalidationRevision
    ) {
      return false;
    }
    state.claimedSessionRevisions.set(
      effect.sessionId,
      effect.invalidationRevision,
    );
    return true;
  }
  if (effect.type === 'reloadSessionsList') {
    if (state.claimedSessionsListRevision === effect.invalidationRevision) {
      return false;
    }
    state.claimedSessionsListRevision = effect.invalidationRevision;
    return true;
  }
  return false;
}

function subscribeMatchingRefreshInvalidations(
  backend: AgentBackend,
  matches: (effect: RefreshUiInvalidation) => boolean,
  reload: () => Promise<boolean>,
): Unsubscribe {
  const state = getState(backend);
  return subscribeRefreshUiEffects(backend, (effect) => {
    if (!matches(effect) || !claimRefreshUiEffect(state, effect)) return;
    let acknowledged = false;
    void reload()
      .then((reloaded) => {
        if (reloaded) {
          acknowledged = true;
        }
      })
      .catch(() => {
        // The reloading consumer surfaces the failure through its own
        // error state; nothing to do here.
      })
      .finally(() => {
        // Consume the invalidation after a single attempt regardless of
        // outcome. Leaving a failed invalidation pending replays it to
        // every new subscriber, which turns any persistent reload
        // failure into an infinite retry + error-alert loop when
        // consumers resubscribe on re-render.
        if (!acknowledged) {
          acknowledgeRefreshUiEffect(backend, effect);
        }
      });
  });
}

export function subscribeSessionRefreshInvalidations(
  backend: AgentBackend,
  sessionId: string,
  reload: () => Promise<boolean>,
): Unsubscribe {
  return subscribeMatchingRefreshInvalidations(
    backend,
    (effect) =>
      effect.type === 'reloadSession' && effect.sessionId === sessionId,
    reload,
  );
}

export function subscribeSessionsListRefreshInvalidations(
  backend: AgentBackend,
  reload: () => Promise<boolean>,
): Unsubscribe {
  return subscribeMatchingRefreshInvalidations(
    backend,
    (effect) => effect.type === 'reloadSessionsList',
    reload,
  );
}

export function emitRefreshUiEffects(backend: AgentBackend, value: unknown): RefreshUiEffect[] {
  const effects = parseRefreshUiEffects(value);
  const state = getState(backend);
  for (const effect of effects) {
    if (effect.type === 'reloadApplicationActions') {
      emitApplicationActionsInvalidated(backend);
      continue;
    }
    const invalidationRevision = ++state.nextRevision;
    const invalidation: RefreshUiInvalidation = {
      ...effect,
      invalidationRevision,
    };
    if (invalidation.type === 'reloadSession') {
      state.pendingSessionRevisions.set(
        invalidation.sessionId,
        invalidationRevision,
      );
      state.claimedSessionRevisions.delete(invalidation.sessionId);
    } else {
      state.pendingSessionsListRevision = invalidationRevision;
      state.claimedSessionsListRevision = null;
    }
    for (const listener of state.listeners) {
      listener(invalidation);
    }
  }
  return effects;
}

export class NotificationUiEffectObserver {
  private readonly seen = new Set<string>();

  constructor(private readonly backend: AgentBackend) {}

  observe(
    scope: 'session' | 'application',
    notification: {
      id: string;
      status: string;
      revision?: number;
      updated_at: string;
      ui_effects?: RefreshUiEffects;
    },
  ): RefreshUiEffect[] {
    const revision = notification.revision ?? notification.updated_at;
    const key = `${scope}:${notification.id}:${String(revision)}`;
    if (this.seen.has(key)) return [];
    this.seen.add(key);
    if (notification.status !== 'pending') return [];
    return emitRefreshUiEffects(this.backend, notification.ui_effects);
  }
}
