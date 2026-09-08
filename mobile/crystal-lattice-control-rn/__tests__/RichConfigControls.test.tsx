import React from "react";
import { fireEvent, render, screen } from "@testing-library/react-native";
import { Text } from "react-native";
import Icon from "react-native-vector-icons/Feather";

import {
  RichConfigDropdownControl,
  RichConfigToggleControl,
  truncatePinnedValue,
} from "@crystal-lattice/frontend-rn-components";

import { ThemeProvider, lightTheme } from "../src/theme";

const renderIcon = ({
  name,
  size,
  color,
}: {
  name: string;
  size: number;
  color: string;
}) => <Icon name={name} size={size} color={color} />;

test("compact dropdown hides its visual label and truncates only display text", () => {
  const iconRenderer = jest.fn(
    ({ name, color }: { name: string; color: string }) => (
      <Text testID="appearance-icon">
        {name}:{color}
      </Text>
    )
  );
  render(
    <ThemeProvider theme={lightTheme}>
      <RichConfigDropdownControl
        control={{
          element: {
            ui_type: "config",
            key: "dummy_rich_ui_appearance",
            type: "dropdown",
            icon: "sliders",
            rich_ui: {},
          } as any,
          richUi: {
            kind: "dropdown",
            label: "Appearance",
            show_label: false,
            placements: ["composer"],
            options: [
              {
                value: "highlight",
                label: "Highlight appearance option",
                icon: "star",
                tone: "highlight",
              },
            ],
          },
        }}
        value="highlight"
        placement="composer"
        maxValueCharacters={10}
        onPress={() => {}}
        renderIcon={iconRenderer}
        testID="compact-model"
      />
    </ThemeProvider>
  );

  expect(screen.queryByText("Appearance:")).toBeNull();
  expect(screen.getByText("Highlight…")).toBeTruthy();
  expect(screen.getByTestId("compact-model").props.accessibilityLabel).toBe(
    "Appearance: Highlight appearance option"
  );
  expect(iconRenderer).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "star",
      color: lightTheme.highlight,
    })
  );
  expect(screen.getByTestId("appearance-icon").props.children).toEqual([
    "star",
    ":",
    lightTheme.highlight,
  ]);
  expect(truncatePinnedValue("Claude", 16)).toBe("Claude");
});

test("compact dropdown uses fallback icon and muted disabled appearance", () => {
  const iconRenderer = jest.fn(
    ({ name, color }: { name: string; color: string }) => (
      <Text testID="disabled-appearance-icon">
        {name}:{color}
      </Text>
    )
  );
  render(
    <ThemeProvider theme={lightTheme}>
      <RichConfigDropdownControl
        control={{
          element: {
            ui_type: "config",
            key: "dummy_rich_ui_appearance",
            type: "dropdown",
            icon: "sliders",
            rich_ui: {},
          } as any,
          richUi: {
            kind: "dropdown",
            label: "Appearance",
            placements: ["composer"],
            options: [{ value: "primary", label: "Primary" }],
          },
        }}
        value="primary"
        disabled
        placement="composer"
        onPress={() => {}}
        renderIcon={iconRenderer}
        testID="disabled-appearance"
      />
    </ThemeProvider>
  );

  expect(iconRenderer).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "sliders",
      color: lightTheme.textMuted,
    })
  );
  expect(
    screen.getByTestId("disabled-appearance").props.accessibilityState.disabled
  ).toBe(true);
});

test("compact dropdown can suppress the outer fallback icon", () => {
  const iconRenderer = jest.fn(() => null);
  render(
    <ThemeProvider theme={lightTheme}>
      <RichConfigDropdownControl
        control={{
          element: {
            ui_type: "config",
            key: "reasoning_effort",
            type: "dropdown",
            icon: "sliders",
            rich_ui: {},
          } as any,
          richUi: {
            kind: "dropdown",
            label: "Reasoning effort",
            show_label: false,
            show_icon: false,
            placements: ["composer"],
            options: [{ value: "high", label: "high" }],
          },
        }}
        value="high"
        placement="composer"
        onPress={() => {}}
        renderIcon={iconRenderer}
        testID="reasoning-effort"
      />
    </ThemeProvider>
  );

  expect(iconRenderer).not.toHaveBeenCalled();
  expect(screen.getByText("high")).toBeTruthy();
});

test.each([
  ["primary", "circle", lightTheme.primary],
  ["highlight", "star", lightTheme.highlight],
  ["warning", "alert-triangle", lightTheme.warning],
  ["success", "check-circle", lightTheme.success],
  ["danger", "x-circle", lightTheme.danger],
  ["muted", "minus-circle", lightTheme.textMuted],
] as const)(
  "renders the dummy %s option with its declared icon and semantic color",
  (tone, icon, expectedColor) => {
    const iconRenderer = jest.fn(() => null);
    render(
      <ThemeProvider theme={lightTheme}>
        <RichConfigDropdownControl
          control={{
            element: {
              ui_type: "config",
              key: "dummy_rich_ui_appearance",
              type: "dropdown",
              icon: "sliders",
              rich_ui: {},
            } as any,
            richUi: {
              kind: "dropdown",
              label: "Appearance",
              placements: ["composer"],
              options: [
                {
                  value: tone,
                  label: tone,
                  icon,
                  tone,
                },
              ],
            },
          }}
          value={tone}
          placement="composer"
          onPress={() => {}}
          renderIcon={iconRenderer}
        />
      </ThemeProvider>
    );

    expect(iconRenderer).toHaveBeenCalledWith({
      name: icon,
      size: 14,
      color: expectedColor,
    });
  }
);

test("compact config toggle exposes its selected state and invokes mutation", () => {
  const onPress = jest.fn();
  const iconRenderer = jest.fn(renderIcon);
  render(
    <ThemeProvider theme={lightTheme}>
      <RichConfigToggleControl
        control={{
          element: {
            ui_type: "config",
            key: "web_search_enabled",
            type: "checkbox",
            icon: "globe",
            rich_ui: {},
          } as any,
          richUi: {
            kind: "toggle",
            label: "Web search",
            show_label: false,
            placements: ["composer"],
            options: [
              {
                value: false,
                label: "Off",
                icon: "globe",
                tone: "primary",
              },
              {
                value: true,
                label: "On",
                icon: "globe",
                tone: "success",
              },
            ],
          },
        }}
        value
        placement="composer"
        onPress={onPress}
        renderIcon={iconRenderer}
        testID="web-search-toggle"
      />
    </ThemeProvider>
  );

  const toggle = screen.getByTestId("web-search-toggle");
  expect(toggle.props.accessibilityLabel).toBe("Web search: On");
  expect(toggle.props.accessibilityState.checked).toBe(true);
  expect(iconRenderer).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "globe",
      color: lightTheme.success,
    })
  );
  fireEvent.press(toggle);
  expect(onPress).toHaveBeenCalledTimes(1);
});
