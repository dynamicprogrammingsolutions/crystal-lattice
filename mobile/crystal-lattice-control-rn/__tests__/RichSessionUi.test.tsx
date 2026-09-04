import React from "react";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { MobileRichSessionUiHarness } from "../src/testing/MobileRichSessionUiHarness";

test("production chat renders and mutates portable rich config and session actions", async () => {
  render(<MobileRichSessionUiHarness />);

  const modelControl = await screen.findByTestId("composer-rich-config-model");
  fireEvent.press(modelControl);
  fireEvent.press(await screen.findByTestId("options-picker-option-claude-b"));
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "claude-b",
    );
  });

  fireEvent.press(screen.getByTestId("composer-rich-config-model"));
  fireEvent.changeText(
    await screen.findByTestId("options-picker-custom-input"),
    "vendor/custom-model",
  );
  fireEvent.press(screen.getByTestId("options-picker-custom-submit"));
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "vendor/custom-model",
    );
  });

  fireEvent.press(screen.getByTestId("composer-rich-config-model"));
  fireEvent.press(await screen.findByTestId("options-picker-reset"));
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "claude-a",
    );
  });

  fireEvent.press(
    await screen.findByTestId("session-rich-action-set_status-composer"),
  );
  fireEvent.press(
    await screen.findByTestId("session-rich-list-set_status-option-done"),
  );
  await waitFor(() => {
    expect(
      screen.getByTestId("rich-session-ui-last-action").props.children,
    ).toBe("set_status:done");
  });
});
