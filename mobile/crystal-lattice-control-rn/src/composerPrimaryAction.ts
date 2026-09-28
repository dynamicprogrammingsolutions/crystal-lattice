export interface SelectPrimaryComposerActionOptions {
  pinnedKeys: readonly string[];
  preferenceKeys: readonly string[];
  isDisabled: (key: string) => boolean;
}

export function selectPrimaryComposerActionKey({
  pinnedKeys,
  preferenceKeys,
  isDisabled,
}: SelectPrimaryComposerActionOptions): string | null {
  const candidates = preferenceKeys.filter((key) => pinnedKeys.includes(key));
  return candidates.find((key) => !isDisabled(key)) ?? candidates[0] ?? null;
}

export function pinnedComposerKeysForBar(
  pinnedKeys: readonly string[],
  primaryKey: string | null,
): string[] {
  return primaryKey == null
    ? [...pinnedKeys]
    : pinnedKeys.filter((key) => key !== primaryKey);
}

export function resolveActiveRequestId(
  liveState: { activeRequestId: string | null } | null | undefined,
  cachedActiveRequestId: string | null | undefined,
): string | null {
  return liveState != null
    ? liveState.activeRequestId
    : cachedActiveRequestId ?? null;
}