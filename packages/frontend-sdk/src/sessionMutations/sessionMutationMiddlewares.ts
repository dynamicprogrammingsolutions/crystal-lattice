import type { BackendMiddleware } from '../runtime/eventedBackend';
import { createSessionScopedSuccessEventMiddleware } from './createSessionScopedSuccessEventMiddleware';
import { SESSION_MUTATION_EVENT_TYPES } from './sessionMutationEventTypes';

export const DEFAULT_SESSION_MUTATION_MIDDLEWARES: BackendMiddleware[] = [
  createSessionScopedSuccessEventMiddleware({
    method: 'setSessionPlugins',
    eventType: SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED,
  }),
  createSessionScopedSuccessEventMiddleware({
    method: 'clearSessionPlugins',
    eventType: SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED,
  }),
  createSessionScopedSuccessEventMiddleware({
    method: 'patchSessionOverrides',
    eventType: SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED,
  }),
  createSessionScopedSuccessEventMiddleware({
    method: 'deleteSessionOverride',
    eventType: SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED,
  }),
  createSessionScopedSuccessEventMiddleware({
    method: 'switchSessionAgent',
    eventType: SESSION_MUTATION_EVENT_TYPES.AGENT_CHANGED,
  }),
];

export function createDefaultSessionMutationMiddlewares(): BackendMiddleware[] {
  return [...DEFAULT_SESSION_MUTATION_MIDDLEWARES];
}
