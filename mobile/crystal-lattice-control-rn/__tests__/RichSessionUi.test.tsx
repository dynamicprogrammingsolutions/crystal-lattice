import React from "react";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

import { MobileRichSessionUiHarness } from "../src/testing/MobileRichSessionUiHarness";

beforeEach(async () => {
  await AsyncStorage.clear();
});

test("production chat renders and mutates portable rich config and session actions", async () => {
  render(<MobileRichSessionUiHarness />);

  const modelControl = await screen.findByTestId("composer-rich-config-model");
  fireEvent.press(modelControl);
  fireEvent.press(
    await screen.findByTestId("options-picker-declared-claude-b")
  );
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "claude-b"
    );
  });

  fireEvent.press(screen.getByTestId("composer-rich-config-model"));
  fireEvent.changeText(
    await screen.findByTestId("options-picker-input"),
    "vendor/custom-model"
  );
  fireEvent.press(
    screen.getByText("Use 'vendor/custom-model' as a custom model ID")
  );
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "vendor/custom-model"
    );
  });

  fireEvent.press(screen.getByTestId("composer-rich-config-model"));
  fireEvent.press(await screen.findByTestId("options-picker-reset"));
  await waitFor(() => {
    expect(screen.getByTestId("rich-session-ui-model").props.children).toBe(
      "claude-a"
    );
  });

  fireEvent.press(
    await screen.findByTestId("session-rich-action-set_status-composer")
  );
  fireEvent.press(
    await screen.findByTestId("session-rich-list-set_status-option-done")
  );
  await waitFor(() => {
    expect(
      screen.getByTestId("rich-session-ui-last-action").props.children
    ).toBe("set_status:done");
  });

  fireEvent.press(screen.getByTestId("composer-rich-config-reasoning_effort"));
  fireEvent.press(await screen.findByTestId("options-picker-declared-high"));

  fireEvent.press(
    screen.getByTestId("composer-rich-config-web_search_enabled")
  );
  await waitFor(() => {
    expect(
      screen.getByTestId("composer-rich-config-web_search_enabled").props
        .accessibilityState.checked
    ).toBe(true);
  });

  fireEvent.press(screen.getByLabelText("Open Composer actions"));
  expect(
    await screen.findByTestId("actions-menu-state-config:web_search_enabled")
  ).toHaveTextContent("On");
  expect(
    screen.getByTestId("actions-menu-action-config:web_search_enabled").props
      .accessibilityLabel
  ).toBe("Enable web search: On");
  fireEvent.press(
    screen.getByTestId("actions-menu-action-config:web_search_enabled")
  );
  await waitFor(() => {
    expect(
      screen.getByTestId("composer-rich-config-web_search_enabled").props
        .accessibilityState.checked
    ).toBe(false);
  });
});

test("mobile composer keeps one draft across inline and maximized editing", async () => {
  render(<MobileRichSessionUiHarness />);

  const inlineInput = await screen.findByTestId("message-composer-input");
  fireEvent.changeText(inlineInput, "Draft before maximize");
  fireEvent.press(screen.getByTestId("composer-maximize"));

  const expandedInput = await screen.findByTestId("expanded-composer-input");
  expect(expandedInput.props.value).toBe("Draft before maximize");
  fireEvent.changeText(expandedInput, "Draft after maximize");
  fireEvent.press(screen.getByTestId("expanded-composer-collapse"));

  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "Draft after maximize"
  );

  const sideButtons = screen.getByTestId("composer-side-buttons");
  expect(
    sideButtons.children.flatMap((child) =>
      typeof child === "object" && child !== null && "props" in child
        ? [(child as any).props.testID]
        : []
    )
  ).toEqual(["composer-primary-action-resend", "composer-send"]);
});

test("primary composer action follows live request state", async () => {
  const rendered = render(<MobileRichSessionUiHarness />);

  await screen.findByTestId("composer-primary-action-resend");

  rendered.rerender(
    <MobileRichSessionUiHarness activeRequestId="request-active" />
  );

  await screen.findByTestId("composer-cancel-request");
  expect(screen.queryByTestId("composer-primary-action-resend")).toBeNull();
});

test("active requests show progress without locking unrelated composer actions", async () => {
  render(<MobileRichSessionUiHarness activeRequestId="request-active" />);

  await screen.findByTestId("composer-send-progress");
  const send = screen.getByTestId("composer-send");
  expect(send.props.accessibilityState).toMatchObject({
    disabled: true,
    busy: true,
  });
  expect(screen.getByTestId("composer-cancel-request").props.disabled).not.toBe(
    true
  );

  fireEvent.changeText(
    screen.getByTestId("message-composer-input"),
    "Append while request runs"
  );
  fireEvent.press(screen.getByLabelText("Open Composer actions"));

  const model = await screen.findByTestId("actions-menu-action-config:model");
  const webSearch = screen.getByTestId(
    "actions-menu-action-config:web_search_enabled"
  );
  const status = screen.getByTestId(
    "actions-menu-action-session_action:set_status"
  );
  const append = screen.getByTestId("actions-menu-action-append");
  const attachment = screen.getByTestId("actions-menu-action-harness-file");
  expect(model.props.disabled).not.toBe(true);
  expect(webSearch.props.disabled).not.toBe(true);
  expect(status.props.disabled).not.toBe(true);
  expect(append.props.disabled).not.toBe(true);
  expect(attachment.props.disabled).not.toBe(true);

  fireEvent.press(webSearch);
  fireEvent.press(screen.getByLabelText("Open Composer actions"));
  expect(
    await screen.findByTestId("actions-menu-state-config:web_search_enabled")
  ).toHaveTextContent("On");
  expect(
    screen.getByTestId("actions-menu-action-cancel").props.disabled
  ).not.toBe(true);
  expect(
    screen.getByTestId("actions-menu-action-softCancel").props.disabled
  ).not.toBe(true);
  expect(screen.getByTestId("actions-menu-action-resend")).toBeTruthy();
  expect(screen.getByTestId("actions-menu-action-append")).toBeTruthy();
  expect(screen.getByTestId("actions-menu-action-appendAs")).toBeTruthy();

  fireEvent.press(screen.getByTestId("actions-menu-close"));
  fireEvent.press(screen.getByTestId("composer-maximize"));
  expect(
    await screen.findByTestId("expanded-composer-send-progress")
  ).toBeTruthy();
});
