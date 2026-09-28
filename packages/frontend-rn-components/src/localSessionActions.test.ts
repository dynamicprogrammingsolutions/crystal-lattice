import { describe, expect, it } from "vitest";

import {
  LOCAL_NOTE_SESSION_ACTION_KEY,
  LOCAL_WATCHLIST_SESSION_ACTION_KEY,
  buildLocalSessionActionDefinitions,
  isLocalSessionActionKey,
} from "./localSessionActions";

describe("local session actions", () => {
  it("builds unpinned state-aware Watchlist and note definitions", () => {
    expect(
      buildLocalSessionActionDefinitions({
        watched: false,
        hasNote: false,
      })
    ).toEqual([
      expect.objectContaining({
        key: LOCAL_WATCHLIST_SESSION_ACTION_KEY,
        label: "Add to Watchlist",
        iconName: "bookmark",
        defaultPinned: false,
      }),
      expect.objectContaining({
        key: LOCAL_NOTE_SESSION_ACTION_KEY,
        label: "Add local note",
        defaultPinned: false,
      }),
    ]);

    expect(
      buildLocalSessionActionDefinitions({
        watched: true,
        hasNote: true,
      })
    ).toEqual([
      expect.objectContaining({
        key: LOCAL_WATCHLIST_SESSION_ACTION_KEY,
        label: "Remove from Watchlist",
        iconName: "x",
      }),
      expect.objectContaining({
        key: LOCAL_NOTE_SESSION_ACTION_KEY,
        label: "Edit local note",
      }),
    ]);
  });

  it("can expose only the local behavior supported by a host surface", () => {
    expect(
      buildLocalSessionActionDefinitions({
        watched: false,
        includeNote: false,
      }).map((action) => action.key)
    ).toEqual([LOCAL_WATCHLIST_SESSION_ACTION_KEY]);
    expect(isLocalSessionActionKey(LOCAL_NOTE_SESSION_ACTION_KEY)).toBe(true);
    expect(isLocalSessionActionKey("toggle_session_pinned")).toBe(false);
  });
});
