import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";

import DevelopmentSettingsModal from "../src/components/DevelopmentSettingsModal";
import { ThemeProvider, lightTheme } from "../src/theme";

test("selects and resets transcript anchor strategies", async () => {
  const setTranscriptAnchorStrategy = jest.fn(async () => {});
  const preferences = {
    settings: { version: 1 as const },
    hydrated: true,
    error: null,
    mode: "http" as const,
    setBridgeMode: jest.fn(async () => {}),
    transcriptAnchorStrategy: "single-flight-anchor" as const,
    setTranscriptAnchorStrategy,
  };
  const screen = render(
    <ThemeProvider theme={lightTheme}>
      <DevelopmentSettingsModal
        visible
        onRequestClose={() => {}}
        preferences={preferences}
      />
    </ThemeProvider>
  );

  fireEvent.press(
    screen.getByTestId("development-transcript-anchor-simple-reload")
  );
  await waitFor(() =>
    expect(setTranscriptAnchorStrategy).toHaveBeenCalledWith("simple-reload")
  );

  fireEvent.press(screen.getByTestId("development-transcript-anchor-reset"));
  await waitFor(() =>
    expect(setTranscriptAnchorStrategy).toHaveBeenCalledWith(
      "single-flight-anchor"
    )
  );
});
