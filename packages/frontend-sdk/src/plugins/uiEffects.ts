import type { AgentBackend } from '../backend/backend';
import type { RefreshUiEffects } from '../types/plugins';
import type { Unsubscribe } from '../util/subscribable';
import { emitApplicationActionsInvalidated } from './applicationActionsInvalidation';

export type RefreshUiEffect =
  | { type: 'reloadSession'; sessionId: string }
  | { type: 'reloadSessionsList' }
  | { type: 'reloadApplicationActions' };

type Listener = (effect: RefreshUiEffect) => void;
const LISTENERS_BY_BACKEND: WeakMap<object, Set<Listener>> = new WeakMap();

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
  let listeners = LISTENERS_BY_BACKEND.get(backend as object);
  if (!listeners) {
    listeners = new Set();
    LISTENERS_BY_BACKEND.set(backend as object, listeners);
  }
  listeners.add(listener);
  return () => listeners?.delete(listener);
}

export function emitRefreshUiEffects(backend: AgentBackend, value: unknown): RefreshUiEffect[] {
  const effects = parseRefreshUiEffects(value);
  for (const effect of effects) {
    if (effect.type === 'reloadApplicationActions') {
      emitApplicationActionsInvalidated(backend);
    }
    for (const listener of LISTENERS_BY_BACKEND.get(backend as object) ?? []) {
      listener(effect);
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
      revision?: number;
      updated_at: string;
      ui_effects?: RefreshUiEffects;
    },
  ): RefreshUiEffect[] {
    const revision = notification.revision ?? notification.updated_at;
    const key = `${scope}:${notification.id}:${String(revision)}`;
    if (this.seen.has(key)) return [];
    this.seen.add(key);
    return emitRefreshUiEffects(this.backend, notification.ui_effects);
  }
}
