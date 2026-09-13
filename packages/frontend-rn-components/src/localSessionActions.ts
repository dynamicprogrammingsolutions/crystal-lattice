import type { SessionActionDefinition } from "./sessionActions";

export const LOCAL_NOTE_SESSION_ACTION_KEY = "localNote";
export const LOCAL_WATCHLIST_SESSION_ACTION_KEY = "localWatchlist";

export type LocalSessionActionKey =
  | typeof LOCAL_NOTE_SESSION_ACTION_KEY
  | typeof LOCAL_WATCHLIST_SESSION_ACTION_KEY;

export function buildLocalSessionActionDefinitions(options: {
  watched: boolean;
  hasNote?: boolean;
  includeNote?: boolean;
  includeWatchlist?: boolean;
}): SessionActionDefinition[] {
  const definitions: SessionActionDefinition[] = [];
  if (options.includeWatchlist !== false) {
    definitions.push({
      key: LOCAL_WATCHLIST_SESSION_ACTION_KEY,
      label: options.watched ? "Remove from Watchlist" : "Add to Watchlist",
      iconName: options.watched ? "x" : "bookmark",
      defaultPinned: false,
      order: 80,
      testID: "session-action-local-watchlist",
    });
  }
  if (options.includeNote !== false) {
    definitions.push({
      key: LOCAL_NOTE_SESSION_ACTION_KEY,
      label: options.hasNote ? "Edit local note" : "Add local note",
      iconName: "edit-3",
      defaultPinned: false,
      order: 81,
      testID: "session-action-local-note",
    });
  }
  return definitions;
}

export function isLocalSessionActionKey(
  value: string
): value is LocalSessionActionKey {
  return (
    value === LOCAL_NOTE_SESSION_ACTION_KEY ||
    value === LOCAL_WATCHLIST_SESSION_ACTION_KEY
  );
}
