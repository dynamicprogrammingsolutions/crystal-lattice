export type DebugTimelineScope = 'app' | 'chat';

export interface DebugTimelineEntry {
  id: string;
  scope: DebugTimelineScope;
  title: string;
  detail: string | null;
  meta?: Record<string, any> | null;
  timestampMs: number;
}

let debugTimelineCounter = 0;

export function createDebugTimelineEntry(params: {
  scope: DebugTimelineScope;
  title: string;
  detail?: string | null;
  meta?: Record<string, any> | null;
  timestampMs?: number;
}): DebugTimelineEntry {
  const timestampMs = params.timestampMs ?? Date.now();
  debugTimelineCounter += 1;
  return {
    id: `debug-${timestampMs}-${debugTimelineCounter}`,
    scope: params.scope,
    title: params.title,
    detail: params.detail ?? null,
    meta: params.meta ?? null,
    timestampMs,
  };
}

export function appendDebugTimelineEntry(
  entries: DebugTimelineEntry[],
  entry: DebugTimelineEntry,
  maxEntries = 200,
): DebugTimelineEntry[] {
  const combined = [...entries, entry];
  if (combined.length <= maxEntries) {
    return combined;
  }
  return combined.slice(combined.length - maxEntries);
}