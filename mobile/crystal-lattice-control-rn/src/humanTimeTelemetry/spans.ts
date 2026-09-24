export interface HumanTimeSpan {
  /** Session id of the surface the user was active on, or null for session-less activity. */
  sessionId: string | null;
  /** First activity of the burst, ISO-8601 UTC. */
  from: string;
  /** Last activity of the burst, ISO-8601 UTC. Idle gaps never enter a span. */
  to: string;
}

export function toIsoUtc(epochMs: number): string {
  return new Date(epochMs).toISOString();
}