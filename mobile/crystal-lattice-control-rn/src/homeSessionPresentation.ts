import {
  deriveSessionListPresentation,
  type SessionSummary,
} from "@crystal-lattice/frontend-sdk";
import type { HomeSessionItem } from "@crystal-lattice/frontend-rn-components";

export interface MobileHomeSessionPresentation {
  title: string;
  subtitle: string | null;
  sessionId: string;
  connectionName: string;
  relativeTime: string;
}

function nonEmptyText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function formatMobileHomeRelativeTime(
  modifiedSeconds: number,
  nowMs = Date.now()
): string {
  const seconds = Math.max(0, Math.floor(nowMs / 1000 - modifiedSeconds));
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function resolveMobileHomeSessionPresentation(
  item: HomeSessionItem,
  nowMs = Date.now()
): MobileHomeSessionPresentation {
  const preview = nonEmptyText(item.summary.preview);
  const suppliedTitle = nonEmptyText(item.summary.presentation?.title);
  const suppliedSubtitle = nonEmptyText(item.summary.presentation?.subtitle);
  const fallbackSummary: SessionSummary = {
    ...item.summary,
    preview: preview ?? "",
    presentation: undefined,
  };
  const fallback = deriveSessionListPresentation(fallbackSummary, []);
  const title = suppliedTitle ?? fallback.title;
  const subtitle =
    suppliedSubtitle ?? (preview && preview !== title ? preview : null);

  return {
    title,
    subtitle,
    sessionId: item.sessionId,
    connectionName: item.connection.name,
    relativeTime: formatMobileHomeRelativeTime(item.summary.modified, nowMs),
  };
}
