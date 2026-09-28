export const DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY = 'clc_desktop_sidebar_width_v1';

export const DESKTOP_SIDEBAR_WIDTH_POLICY = Object.freeze({
  defaultWidth: 340,
  minimumWidth: 260,
  maximumWidth: 520,
  adjustmentStep: 20,
  minimumMainWidth: 480,
  activityRailWidth: 46,
  activityPanelSeparatorWidth: 1,
  resizeHandleWidth: 9,
});

export interface DesktopSidebarWidthBounds {
  minimumWidth: number;
  maximumWidth: number;
}

function finiteNumber(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value !== 'string' || value.trim() === '') {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

export function normalizeDesktopSidebarWidth(value: unknown): number {
  const parsed = finiteNumber(value);
  const rounded =
    parsed === null
      ? DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth
      : Math.round(parsed);
  return clamp(
    rounded,
    DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
    DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
  );
}

export function getDesktopSidebarWidthBounds(
  shellWidth: number | null,
): DesktopSidebarWidthBounds {
  if (shellWidth === null || !Number.isFinite(shellWidth)) {
    return {
      minimumWidth: DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
      maximumWidth: DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
    };
  }

  const fixedWidth =
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth;
  const availableWidth = Math.floor(
    shellWidth - fixedWidth - DESKTOP_SIDEBAR_WIDTH_POLICY.minimumMainWidth,
  );

  return {
    minimumWidth: DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
    maximumWidth: clamp(
      availableWidth,
      DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
      DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
    ),
  };
}

export function resolveDesktopSidebarWidth(
  preferredWidth: unknown,
  shellWidth: number | null,
): number {
  const bounds = getDesktopSidebarWidthBounds(shellWidth);
  return clamp(
    normalizeDesktopSidebarWidth(preferredWidth),
    bounds.minimumWidth,
    bounds.maximumWidth,
  );
}

export function adjustDesktopSidebarWidth(
  currentWidth: number,
  direction: -1 | 1,
  shellWidth: number | null,
): number {
  return resolveDesktopSidebarWidth(
    currentWidth + direction * DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep,
    shellWidth,
  );
}

export function parsePersistedDesktopSidebarWidth(raw: string | null): number {
  return normalizeDesktopSidebarWidth(raw);
}

export function serializeDesktopSidebarWidth(width: number): string {
  return String(normalizeDesktopSidebarWidth(width));
}
