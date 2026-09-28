export interface ResolveComposerPrimaryLayoutOptions {
  pinnedKeys: readonly string[];
  preferenceKeys: readonly string[];
  requestActive: boolean;
}

export interface ComposerPrimaryLayout {
  alternatingCancelKey: string | null;
  primaryKey: string | null;
  hiddenKey: string | null;
}

export function resolveComposerPrimaryLayout({
  pinnedKeys,
  preferenceKeys,
  requestActive,
}: ResolveComposerPrimaryLayoutOptions): ComposerPrimaryLayout {
  const pinned = new Set(pinnedKeys);
  const alternatingCancelKey = pinned.has('resend')
    ? pinned.has('cancel')
      ? 'cancel'
      : pinned.has('softCancel')
        ? 'softCancel'
        : null
    : null;

  if (alternatingCancelKey != null) {
    return {
      alternatingCancelKey,
      primaryKey: requestActive ? alternatingCancelKey : 'resend',
      hiddenKey: requestActive ? 'resend' : alternatingCancelKey,
    };
  }

  return {
    alternatingCancelKey: null,
    primaryKey:
      preferenceKeys.find((key) => pinned.has(key)) ?? null,
    hiddenKey: null,
  };
}

export function pinnedComposerKeysForBar(
  pinnedKeys: readonly string[],
  layout: Pick<ComposerPrimaryLayout, 'primaryKey' | 'hiddenKey'>,
): string[] {
  return pinnedKeys.filter(
    (key) => key !== layout.primaryKey && key !== layout.hiddenKey,
  );
}

export function resolveActiveRequestId(
  liveState: { activeRequestId: string | null } | null | undefined,
  cachedActiveRequestId: string | null | undefined,
): string | null {
  return liveState != null
    ? liveState.activeRequestId
    : cachedActiveRequestId ?? null;
}