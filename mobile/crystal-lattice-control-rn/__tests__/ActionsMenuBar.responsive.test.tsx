import React from "react";
import { StyleSheet, Text } from "react-native";
import { fireEvent, render } from "@testing-library/react-native";

import {
  ActionsMenuBar,
  type ActionDefinition,
} from "@crystal-lattice/frontend-rn-components";

import { ThemeProvider, lightTheme } from "../src/theme";

const actions: ActionDefinition[] = Array.from({ length: 8 }, (_, index) => ({
  key: `action-${index}`,
  label: `Action ${index}`,
  iconName: "circle",
  testID: `pinned-action-${index}`,
}));

test("limits compact pins while keeping the overflow menu complete", () => {
  const visibleLimit = actions.length - 3;
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Responsive actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        maxPinnedActionsForBar={visibleLimit}
        onChangePinned={() => {}}
        onAction={() => {}}
        menuButtonTestID="responsive-actions-menu"
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(rendered.getByTestId("actions-menu-overflow-slot")).toBeTruthy();
  for (let index = 0; index < visibleLimit; index += 1) {
    expect(rendered.getByTestId(`pinned-action-${index}`)).toBeTruthy();
  }
  for (let index = visibleLimit; index < actions.length; index += 1) {
    expect(rendered.queryByTestId(`pinned-action-${index}`)).toBeNull();
  }

  fireEvent.press(rendered.getByTestId("responsive-actions-menu"));

  for (const action of actions) {
    expect(
      rendered.getByTestId(`actions-menu-action-${action.key}`)
    ).toBeTruthy();
    expect(rendered.getByTestId(`actions-menu-pin-${action.key}`)).toBeTruthy();
  }
});

test("enables an explicitly positioned second pinned row", () => {
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Two row actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        pinnedRows={2}
        secondPinnedRowPlacement="below"
        onChangePinned={() => {}}
        onAction={() => {}}
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(
    StyleSheet.flatten(
      rendered.getByTestId("actions-menu-pinned-viewport").props.style
    )
  ).toMatchObject({
    flexWrap: "wrap",
    justifyContent: "flex-end",
    minHeight: 40,
    maxHeight: 82,
  });
  expect(
    StyleSheet.flatten(rendered.getByTestId("actions-menu-bar").props.style)
  ).toMatchObject({
    alignSelf: "stretch",
    justifyContent: "flex-end",
  });
  expect(
    StyleSheet.flatten(
      rendered.getByTestId("actions-menu-overflow-slot").props.style
    )
  ).toMatchObject({ alignSelf: "flex-start" });

  rendered.rerender(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Two row actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        pinnedRows={2}
        secondPinnedRowPlacement="above"
        onChangePinned={() => {}}
        onAction={() => {}}
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(
    StyleSheet.flatten(
      rendered.getByTestId("actions-menu-pinned-viewport").props.style
    )
  ).toMatchObject({ flexWrap: "wrap-reverse" });
  expect(
    StyleSheet.flatten(
      rendered.getByTestId("actions-menu-overflow-slot").props.style
    )
  ).toMatchObject({ alignSelf: "flex-end" });
});

test("renders neutral menu state text and invokes a toggle in one click", () => {
  const onAction = jest.fn();
  const renderIcon = jest.fn(
    ({ name, color }: { name: string; color: string }) => (
      <Text testID="ordinary-action-icon">
        {name}:{color}
      </Text>
    )
  );
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Composer actions"
        baseActions={[
          {
            key: "config:web_search_enabled",
            label: "Enable web search",
            iconName: "globe",
            menuStateLabel: "On",
          },
        ]}
        pinned={[]}
        onChangePinned={() => {}}
        onAction={onAction}
        menuButtonTestID="composer-actions-menu"
        renderIcon={renderIcon}
      />
    </ThemeProvider>
  );

  fireEvent.press(rendered.getByTestId("composer-actions-menu"));

  expect(
    rendered.getByTestId("actions-menu-state-config:web_search_enabled").props
      .children
  ).toBe("On");
  const action = rendered.getByTestId(
    "actions-menu-action-config:web_search_enabled"
  );
  expect(action.props.accessibilityLabel).toBe("Enable web search: On");
  expect(renderIcon).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "globe",
      color: lightTheme.primary,
    })
  );
  fireEvent.press(action);

  expect(onAction).toHaveBeenCalledWith("config:web_search_enabled");
  expect(
    rendered.queryByTestId("actions-menu-state-config:web_search_enabled")
  ).toBeNull();
});

test("lets a long state use the width left by a short title and truncates adaptively", () => {
  const longValue =
    "anthropic/claude-sonnet-a-very-long-custom-model-identifier";
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Composer actions"
        baseActions={[
          {
            key: "config:model",
            label: "Model",
            iconName: "cpu",
            menuStateLabel: longValue,
          },
          {
            key: "config:long",
            label: "A deliberately long ordinary configuration title",
            iconName: "sliders",
            menuStateLabel: "A deliberately long selected value",
          },
        ]}
        pinned={[]}
        onChangePinned={() => {}}
        onAction={() => {}}
        menuButtonTestID="long-actions-menu"
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  fireEvent.press(rendered.getByTestId("long-actions-menu"));

  const modelTitle = rendered.getByText("Model");
  const modelState = rendered.getByTestId("actions-menu-state-config:model");
  expect(modelTitle.props.numberOfLines).toBe(1);
  expect(modelTitle.props.ellipsizeMode).toBe("tail");
  expect(modelState.props.numberOfLines).toBe(1);
  expect(modelState.props.ellipsizeMode).toBe("tail");
  expect(StyleSheet.flatten(modelState.props.style)).toMatchObject({
    flexShrink: 1,
    minWidth: 0,
    textAlign: "right",
  });
  expect(
    rendered.getByTestId("actions-menu-action-config:model").props
      .accessibilityLabel
  ).toBe(`Model: ${longValue}`);

  const longTitle = rendered.getByText(
    "A deliberately long ordinary configuration title"
  );
  expect(StyleSheet.flatten(longTitle.props.style)).toMatchObject({
    flexShrink: 1,
    minWidth: 0,
  });
});
