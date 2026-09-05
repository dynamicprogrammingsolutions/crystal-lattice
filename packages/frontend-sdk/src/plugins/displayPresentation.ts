import type { AgentBackend } from '../backend/backend';
import type { ActionDisplayPayload } from '../types/plugins';
import type { NotificationExpectedRevision } from '../types/notifications';
import type { Unsubscribe } from '../util/subscribable';

export type DisplaySourceKind =
  | 'application_notification'
  | 'session_notification'
  | 'action_response';
export type DisplayPresentation = 'banner' | 'inline' | 'modal';
export type DisplayPresentationHost = 'mobile' | 'desktop';
export type DisplayOwnership =
  | { scope: 'connection'; connectionId?: string | null }
  | { scope: 'session'; connectionId?: string | null; sessionId: string };

export interface DisplayEnvelope {
  id: string;
  source: DisplaySourceKind;
  ownershipScope?: 'connection' | 'session';
  connectionId?: string | null;
  sessionId?: string | null;
  display: ActionDisplayPayload;
  createdAt?: string;
  updatedAt?: string;
  sourceKey?: string;
  notificationRevision?: NotificationExpectedRevision;
}

type DisplayListener = (envelope: DisplayEnvelope) => void;
const DISPLAY_LISTENERS = new WeakMap<object, Set<DisplayListener>>();

export function normalizeDisplayEnvelope(options: {
  display: ActionDisplayPayload;
  source: DisplaySourceKind;
  ownershipScope?: 'connection' | 'session';
  connectionId?: string | null;
  sessionId?: string | null;
  id?: string;
  sourceKey?: string;
  createdAt?: string;
  updatedAt?: string;
  notificationRevision?: NotificationExpectedRevision;
}): DisplayEnvelope {
  const fallback: DisplayPresentation =
    options.source === 'action_response'
      ? 'modal'
      : options.source === 'session_notification'
        ? 'inline'
        : 'banner';
  const presentation = options.display.presentation ?? fallback;
  if (presentation !== 'banner' && presentation !== 'inline' && presentation !== 'modal') {
    throw new Error(`Unsupported display presentation: ${String(presentation)}`);
  }
  if (options.source === 'application_notification' && presentation === 'inline') {
    throw new Error('Application notifications do not support inline presentation');
  }
  const id =
    options.id ??
    options.display.display_id ??
    `${options.source}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
  return {
    id,
    source: options.source,
    ownershipScope: options.ownershipScope,
    connectionId: options.connectionId,
    sessionId: options.sessionId,
    sourceKey: options.sourceKey,
    createdAt: options.createdAt,
    updatedAt: options.updatedAt,
    notificationRevision: options.notificationRevision,
    display: { ...options.display, display_id: id, presentation },
  };
}

export function displayEnvelopeLifecycleKey(envelope: DisplayEnvelope): string {
  return `${envelope.connectionId ?? ''}:${envelope.source}:${envelope.id}`;
}

export function displayEnvelopeRevisionKey(envelope: DisplayEnvelope): string {
  return `${displayEnvelopeLifecycleKey(envelope)}:${envelope.updatedAt ?? envelope.display.display_id ?? envelope.id}`;
}

export function classifyDisplayEnvelope(envelope: DisplayEnvelope): DisplayOwnership {
  if (envelope.ownershipScope === 'connection') {
    return {
      scope: 'connection',
      connectionId: envelope.connectionId,
    };
  }
  if (envelope.source === 'session_notification') {
    if (!envelope.sessionId) {
      throw new Error('Session notification display requires sessionId');
    }
    return {
      scope: 'session',
      connectionId: envelope.connectionId,
      sessionId: envelope.sessionId,
    };
  }
  if (
    envelope.ownershipScope === 'session' ||
    (envelope.source === 'action_response' && envelope.sessionId)
  ) {
    if (!envelope.sessionId) {
      throw new Error('Session-owned display requires sessionId');
    }
    return {
      scope: 'session',
      connectionId: envelope.connectionId,
      sessionId: envelope.sessionId,
    };
  }
  return {
    scope: 'connection',
    connectionId: envelope.connectionId,
  };
}

export function normalizeDisplayEnvelopeForHost(
  envelope: DisplayEnvelope,
  host: DisplayPresentationHost,
): DisplayEnvelope {
  if (
    host === 'desktop' &&
    envelope.display.presentation === 'modal' &&
    envelope.source !== 'action_response'
  ) {
    return {
      ...envelope,
      display: {
        ...envelope.display,
        presentation: 'inline',
      },
    };
  }
  return envelope;
}

export function subscribeDisplayPresentation(
  backend: AgentBackend,
  listener: DisplayListener,
): Unsubscribe {
  let listeners = DISPLAY_LISTENERS.get(backend as object);
  if (!listeners) {
    listeners = new Set();
    DISPLAY_LISTENERS.set(backend as object, listeners);
  }
  listeners.add(listener);
  return () => DISPLAY_LISTENERS.get(backend as object)?.delete(listener);
}

export function emitDisplayPresentation(
  backend: AgentBackend,
  envelope: DisplayEnvelope,
): void {
  for (const listener of DISPLAY_LISTENERS.get(backend as object) ?? []) {
    listener(envelope);
  }
}