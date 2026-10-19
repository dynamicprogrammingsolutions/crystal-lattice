export type TranscriptAnchorStrategy =
  | "simple-reload"
  | "mobile-anchor-v1"
  | "single-flight-anchor";

export const DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY =
  "single-flight-anchor" as const satisfies TranscriptAnchorStrategy;

export const TRANSCRIPT_ANCHOR_STRATEGY_OPTIONS: ReadonlyArray<{
  value: TranscriptAnchorStrategy;
  label: string;
  description: string;
}> = [
  {
    value: "single-flight-anchor",
    label: "Single-flight anchor — Product default",
    description:
      "Preserves the visible message with one bounded retry operation.",
  },
  {
    value: "simple-reload",
    label: "Simple reload — Diagnostic baseline",
    description:
      "Loads the requested range without explicit viewport restoration.",
  },
  {
    value: "mobile-anchor-v1",
    label: "Mobile anchor v1 — Legacy diagnostic",
    description:
      "Uses the original mobile retry implementation for controlled comparison.",
  },
];

export function isTranscriptAnchorStrategy(
  value: unknown
): value is TranscriptAnchorStrategy {
  return (
    value === "simple-reload" ||
    value === "mobile-anchor-v1" ||
    value === "single-flight-anchor"
  );
}

export function normalizeTranscriptAnchorStrategy(
  value: unknown
): TranscriptAnchorStrategy {
  return isTranscriptAnchorStrategy(value)
    ? value
    : DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY;
}
