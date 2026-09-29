import type { HumanTimeSpan } from "./spans";
import type { HumanTimeUploadEvent } from "./uploader";

export type HumanTimeDiagnosticUploadStatus =
  "pending" | "uploading" | "uploaded" | "retrying" | "failed";

export interface HumanTimeDiagnosticEntry extends HumanTimeSpan {
  uploadStatus: HumanTimeDiagnosticUploadStatus;
  error: string | null;
}

export const RECENT_HUMAN_TIME_DIAGNOSTIC_ENTRY_LIMIT = 10;

export function humanTimeDiagnosticSpanKey(span: HumanTimeSpan): string {
  return `${span.sessionId ?? ""}\u0000${span.from}\u0000${span.to}`;
}

export function newestHumanTimeDiagnosticEntries(
  entries: HumanTimeDiagnosticEntry[],
): HumanTimeDiagnosticEntry[] {
  return [...entries]
    .sort((left, right) => right.to.localeCompare(left.to))
    .slice(0, RECENT_HUMAN_TIME_DIAGNOSTIC_ENTRY_LIMIT);
}

export function mergePendingHumanTimeDiagnosticEntries(
  current: HumanTimeDiagnosticEntry[],
  pending: HumanTimeSpan[],
): HumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map((entry) => [humanTimeDiagnosticSpanKey(entry), entry]),
  );
  for (const span of pending) {
    const key = humanTimeDiagnosticSpanKey(span);
    if (!entries.has(key)) {
      entries.set(key, { ...span, uploadStatus: "pending", error: null });
    }
  }
  return newestHumanTimeDiagnosticEntries([...entries.values()]);
}

export function updateHumanTimeDiagnosticEntries(
  current: HumanTimeDiagnosticEntry[],
  spans: HumanTimeSpan[],
  uploadStatus: HumanTimeDiagnosticUploadStatus,
  error: string | null,
): HumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map((entry) => [humanTimeDiagnosticSpanKey(entry), entry]),
  );
  for (const span of spans) {
    entries.set(humanTimeDiagnosticSpanKey(span), {
      ...span,
      uploadStatus,
      error,
    });
  }
  return newestHumanTimeDiagnosticEntries([...entries.values()]);
}

export function humanTimeDiagnosticUploadStatus(
  outcome: HumanTimeUploadEvent["outcome"],
): HumanTimeDiagnosticUploadStatus {
  switch (outcome) {
    case "uploading":
      return "uploading";
    case "flushed":
      return "uploaded";
    case "partial-failure":
      return "failed";
    case "transient-failure":
      return "retrying";
    case "definitive-failure":
      return "failed";
  }
}
