import type { SdkEvent } from '../runtime/sdkEvent';
import type { SessionSummary } from '../types/sessions';

export const SESSION_MUTATION_EVENT_TYPES = {
  PLUGINS_CHANGED: 'session.plugins.changed',
  OVERRIDES_CHANGED: 'session.overrides.changed',
  AGENT_CHANGED: 'session.agent.changed',
  SUMMARY_UPSERTED: 'session.summary.upserted',
} as const;

export type SessionMutationEventType =
  (typeof SESSION_MUTATION_EVENT_TYPES)[keyof typeof SESSION_MUTATION_EVENT_TYPES];

export interface SessionScopedSdkEvent extends SdkEvent {
  sessionId: string;
}

export type SessionPluginsChangedEvent = SessionScopedSdkEvent & {
  type: typeof SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED;
};

export type SessionOverridesChangedEvent = SessionScopedSdkEvent & {
  type: typeof SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED;
};

export type SessionAgentChangedEvent = SessionScopedSdkEvent & {
  type: typeof SESSION_MUTATION_EVENT_TYPES.AGENT_CHANGED;
};

export type SessionSummaryUpsertedEvent =
  | (SessionScopedSdkEvent & {
      type: typeof SESSION_MUTATION_EVENT_TYPES.SUMMARY_UPSERTED;
    })
  | (SessionScopedSdkEvent & {
      type: typeof SESSION_MUTATION_EVENT_TYPES.SUMMARY_UPSERTED;
      summary: SessionSummary;
    });

export type SessionMutationEvent =
  | SessionPluginsChangedEvent
  | SessionOverridesChangedEvent
  | SessionAgentChangedEvent
  | SessionSummaryUpsertedEvent;
