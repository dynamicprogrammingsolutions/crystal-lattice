import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import type { KeyValueStore } from "@crystal-lattice/frontend-sdk";

import SessionsScreen from "../SessionsScreen";
import { HomeWorkspaceProvider } from "../HomeWorkspaceContext";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import { ThemeProvider, lightTheme } from "../theme";

const store: KeyValueStore = {
  get: async () => null,
  set: async () => {},
  delete: async () => {},
};

describe("SessionsScreen local notes and request status", () => {
  it("edits a permanent note while offline and renders the shared status badge", async () => {
    const screen = render(
      <ThemeProvider theme={lightTheme}>
        <PinnedActionsProvider>
          <HomeWorkspaceProvider store={store}>
            <SessionsScreen
              backend={null}
              connectionId="connection"
              cachedSessions={[
                {
                  session_id: "shared",
                  modified: 10,
                  preview: "Session preview",
                },
              ]}
              lastLoadedAt={1}
              isActive
              onUpdateCache={() => {}}
              onSelectSession={() => {}}
              requestStatuses={{
                shared: {
                  session_id: "shared",
                  request_id: null,
                  state: "interrupted",
                  basis: "session_tail",
                  session_modified: 10,
                },
              }}
            />
          </HomeWorkspaceProvider>
        </PinnedActionsProvider>
      </ThemeProvider>
    );
    await waitFor(() =>
      expect(screen.getByTestId("session-actions-menu-shared")).toBeTruthy()
    );

    fireEvent.press(screen.getByTestId("session-actions-menu-shared"));
    fireEvent.press(screen.getByText("Add local note"));
    fireEvent.changeText(
      screen.getByTestId("session-note-input"),
      "Available from Sessions"
    );
    fireEvent.press(screen.getByTestId("session-note-save"));

    await waitFor(() =>
      expect(
        screen.getByTestId("session-local-note-shared").props.children
      ).toBe("Available from Sessions")
    );
    expect(
      screen.getByTestId("session-request-status-shared").props
        .accessibilityLabel
    ).toBe("Request status: Interrupted");

    fireEvent.press(screen.getByTestId("session-actions-menu-shared"));
    fireEvent.press(screen.getByText("Add to Watchlist"));
    fireEvent.press(screen.getByTestId("session-actions-menu-shared"));
    await waitFor(() =>
      expect(screen.getByText("Remove from Watchlist")).toBeTruthy()
    );
  });
});
