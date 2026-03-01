import type { SdkEvent } from '../runtime/sdkEvent';

export function isEventForSession(ev: SdkEvent, scopeKey: string, sessionId: string): boolean {
  const rawSessionId = ev['sessionId'];
  return ev.scopeKey === scopeKey && typeof rawSessionId === 'string' && rawSessionId === sessionId;
}
