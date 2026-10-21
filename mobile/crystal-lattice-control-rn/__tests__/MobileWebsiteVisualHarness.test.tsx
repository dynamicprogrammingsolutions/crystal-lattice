import React from "react";
import {
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react-native";
import * as sharedComponents from "@crystal-lattice/frontend-rn-components";
import Icon from "react-native-vector-icons/Feather";

import { MobileWebsiteVisualHarness } from "../src/testing/MobileWebsiteVisualHarness";

test("the Vibe illustration renders a first System message, user request, and initial reasoning", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="vibe"
      clcWebsiteVisualTheme="light"
    />
  );
  fireEvent.press(screen.getByTestId("website-visual-open-vibe"));
  expect(await screen.findByText("[0] System")).toBeTruthy();
  expect(screen.getByTestId("message-bubble-1")).toBeTruthy();
  fireEvent.press(screen.getByTestId("assistant-reasoning-disclosure-2"));
  expect(
    await screen.findByTestId("assistant-reasoning-content-2")
  ).toBeTruthy();
});

test("the refreshed runtime fixture reaches the real session menu with its supported title icon", async () => {
  // The suite default stubs this whole bar. Use its actual public consumer
  // for this fixture regression, retaining the suite's native-package mocks.
  const bar = jest
    .spyOn(sharedComponents, "SessionActionsBar")
    .mockImplementation(
      jest.requireActual("@crystal-lattice/frontend-rn-components")
        .SessionActionsBar
    );
  try {
    const screen = render(
      <MobileWebsiteVisualHarness
        clcWebsiteVisualKind="actions"
        clcWebsiteVisualTheme="light"
      />
    );
    fireEvent.press(screen.getByTestId("website-visual-open-actions"));
    fireEvent.press(await screen.findByTestId("session-actions-menu"));
    const action = await screen.findByTestId(
      "actions-menu-action-generate_title_from_view"
    );
    expect(screen.getByText("Generate title")).toBeTruthy();
    expect(
      action.findAll((node) => node.type === Icon && node.props.name === "zap")
    ).toHaveLength(1);
  } finally {
    bar.mockRestore();
  }
});

test.each([
  ["compiled", "Compiled system message"],
  ["cost", "Cost report"],
] as const)(
  "renders the generated %s action fixture through the production modal",
  async (kind, title) => {
    const screen = render(
      <MobileWebsiteVisualHarness
        clcWebsiteVisualKind={kind}
        clcWebsiteVisualTheme="light"
      />
    );

    fireEvent.press(screen.getByTestId(`website-visual-open-${kind}`));

    await waitFor(() => {
      expect(screen.getByTestId(`website-${kind}-action-display`)).toBeTruthy();
      expect(screen.getByText(title)).toBeTruthy();
    });
  }
);

test("renders the authored system template through the production transcript", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="system-template"
      clcWebsiteVisualTheme="light"
    />
  );

  fireEvent.press(screen.getByTestId("website-visual-open-system-template"));

  await waitFor(() => {
    expect(
      screen.getByDisplayValue(
        "You are {{AGENT_TITLE}}. Follow the project guidance below before acting.\n\n{{PROJECT_GUIDANCE}}\n\nUse the enabled {{TOOLSET_NAME}} tools and report assumptions explicitly."
      )
    ).toBeTruthy();
    expect(screen.getByText("[0] System")).toBeTruthy();
  });
});

test("renders the active request state through the production composer", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="composer-active"
      clcWebsiteVisualTheme="light"
    />
  );

  fireEvent.press(screen.getByTestId("website-visual-open-composer-active"));

  await waitFor(() => {
    expect(screen.getByTestId("composer-send-progress")).toBeTruthy();
    expect(
      screen.getByDisplayValue(
        "Append a validation note while the current request finishes."
      )
    ).toBeTruthy();
  });
});

test("renders the Starlette message actions through the production action menu", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="message-actions"
      clcWebsiteVisualTheme="light"
    />
  );

  fireEvent.press(screen.getByTestId("website-visual-open-message-actions"));

  const terminalMessage = await waitFor(() =>
    screen.getByTestId("message-bubble-6")
  );
  const terminalMessageActions = within(terminalMessage).getByTestId(
    "message-actions-menu"
  );
  fireEvent.press(terminalMessageActions);

  await waitFor(() => {
    expect(screen.getByText("Message actions")).toBeTruthy();
    expect(screen.getByText("Fork here")).toBeTruthy();
    expect(screen.getByText("Copy message")).toBeTruthy();
  });
});

test("renders deterministic request states in the workspace candidate", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="workspaces"
      clcWebsiteVisualTheme="light"
    />
  );

  await waitFor(() => {
    expect(
      screen.getByTestId("session-request-status-starlette-compatibility")
    ).toBeTruthy();
    expect(screen.getByText("Plan a Starlette compatibility fix")).toBeTruthy();
    expect(screen.getByText("In progress")).toBeTruthy();
    expect(screen.getByText("Not started")).toBeTruthy();
    expect(screen.getByText("Completed")).toBeTruthy();
  });
});

test("renders a local Watchlist and recent-session workspace", async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="home"
      clcWebsiteVisualTheme="light"
    />
  );

  await waitFor(() => {
    expect(
      screen.getByTestId(
        "home-watchlist-tile-local-workspace-starlette-compatibility"
      )
    ).toBeTruthy();
    expect(screen.getByText("Recent Sessions")).toBeTruthy();
  });
});
