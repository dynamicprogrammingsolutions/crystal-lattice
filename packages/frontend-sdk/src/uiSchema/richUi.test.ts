import { describe, expect, it } from "vitest";

import {
  getDefaultPinnedConfigRichUiKeys,
  isSessionActionPlacedAt,
  normalizeConfigRichUiElement,
  normalizeSessionActionRichUiElement,
  selectConfigRichUiControls,
} from "./richUi";

function modelElement(overrides: Record<string, unknown> = {}) {
  return {
    ui_type: "config",
    type: "dropdown",
    key: "model",
    label: "Full model label",
    options: [{ value: "claude-a", label: "Claude A" }],
    allow_custom_value: true,
    rich_ui: {
      kind: "dropdown",
      label: "Model",
      options: [{ value: "claude-a", label: "Claude A" }],
      allow_custom_value: true,
      custom_value_label: "Other model…",
      custom_value_placeholder: "Enter a model ID",
      placements: ["composer"],
      default_pinned: true,
      icon: "cpu",
    },
    ...overrides,
  };
}

describe("config rich UI", () => {
  it("normalizes a self-contained model dropdown", () => {
    const result = normalizeConfigRichUiElement(modelElement());

    expect(result.diagnostics).toEqual([]);
    expect(result.value?.rich_ui).toEqual({
      kind: "dropdown",
      label: "Model",
      options: [{ value: "claude-a", label: "Claude A" }],
      allow_custom_value: true,
      custom_value_label: "Other model…",
      custom_value_placeholder: "Enter a model ID",
      placements: ["composer"],
      default_pinned: true,
      icon: "cpu",
    });
  });

  it("allows a text settings fallback with a custom-only rich dropdown", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({
        type: "text",
        options: undefined,
        rich_ui: {
          kind: "dropdown",
          label: "Model",
          options: [],
          allow_custom_value: true,
          custom_value_label: "Other model…",
          placements: ["composer"],
        },
      }),
    );

    expect(result.value?.rich_ui).toMatchObject({
      kind: "dropdown",
      options: [],
      allow_custom_value: true,
    });
  });

  it("does not inherit missing presentation fields from the config element", () => {
    const raw = modelElement();
    (raw.rich_ui as Record<string, unknown>).label = undefined;

    const result = normalizeConfigRichUiElement(raw);

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain("rich_ui.dropdown.label");
  });

  it("requires custom entry on both the config and rich declarations", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({ allow_custom_value: false }),
    );

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain(
      "containing config element",
    );
  });

  it("rejects duplicate dropdown values", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({
        rich_ui: {
          kind: "dropdown",
          label: "Model",
          options: [
            { value: "same", label: "One" },
            { value: "same", label: "Two" },
          ],
          placements: ["composer"],
        },
      }),
    );

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain("duplicated");
  });

  it("selects controls by placement and derives default pinning", () => {
    const selected = selectConfigRichUiControls(
      [
        modelElement(),
        modelElement({
          key: "header_model",
          rich_ui: {
            kind: "dropdown",
            label: "Header model",
            options: [{ value: "a", label: "A" }],
            placements: ["session_header"],
          },
        }),
      ],
      "composer",
    );

    expect(selected.controls.map((control) => control.element.key)).toEqual([
      "model",
    ]);
    expect(getDefaultPinnedConfigRichUiKeys(selected.controls)).toEqual([
      "model",
    ]);
  });

  it("transports unknown future kinds without selecting a renderer", () => {
    const result = normalizeConfigRichUiElement({
      ui_type: "config",
      type: "text",
      key: "future",
      rich_ui: { kind: "future_control", label: "Future" },
    });

    expect(result.value?.rich_ui).toEqual({
      kind: "future_control",
      label: "Future",
    });
  });
});

describe("session action rich UI", () => {
  it("normalizes existing list semantics and defaults to the header", () => {
    const result = normalizeSessionActionRichUiElement({
      ui_type: "session_action",
      plugin: "status",
      id: "set_status",
      label: "Set status",
      action_id: "set_status",
      dialog: { kind: "none" },
      rich_ui: {
        kind: "list",
        value_path: "metadata.status",
        input_name: "status",
        options: [{ value: "todo", label: "To do" }],
      },
    });

    expect(result.diagnostics).toEqual([]);
    expect(result.value).not.toBeNull();
    expect(isSessionActionPlacedAt(result.value!, "session_header")).toBe(true);
    expect(isSessionActionPlacedAt(result.value!, "composer")).toBe(false);
  });

  it("honors explicit composer placement", () => {
    const result = normalizeSessionActionRichUiElement({
      ui_type: "session_action",
      plugin: "status",
      id: "set_status",
      label: "Set status",
      action_id: "set_status",
      rich_ui: {
        kind: "list",
        value_path: "metadata.status",
        input_name: "status",
        placements: ["composer"],
        options: [{ value: "todo", label: "To do" }],
      },
    });

    expect(result.value).not.toBeNull();
    expect(isSessionActionPlacedAt(result.value!, "composer")).toBe(true);
    expect(isSessionActionPlacedAt(result.value!, "session_header")).toBe(
      false,
    );
  });
});
