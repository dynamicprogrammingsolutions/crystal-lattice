import { describe, expect, it } from "vitest";

import {
  createConfigDropdownSuggestionEngine,
  getDefaultPinnedConfigRichUiKeys,
  isSessionActionPlacedAt,
  normalizeConfigDropdownPresentation,
  normalizeConfigRichUiElement,
  normalizeSessionActionRichUiElement,
  resolveConfigRichUiMenuStateLabel,
  resolveConfigRichToggleOption,
  selectConfigRichUiControls,
} from "./richUi";

function modelElement(overrides: Record<string, unknown> = {}) {
  return {
    ui_type: "config",
    type: "dropdown",
    key: "model",
    label: "Full model label",
    icon: "cpu",
    options: [{ value: "claude-a", label: "Claude A" }],
    placeholder: "Search models or enter a model ID",
    custom_value: {
      enabled: true,
      pattern: "^[^\\s]+$",
      option_label: "Use '{value}' as a custom model ID",
    },
    rich_ui: {
      kind: "dropdown",
      label: "Model",
      show_label: false,
      options: [{ value: "claude-a", label: "Claude A" }],
      placeholder: "Search models or enter a model ID",
      custom_value: {
        enabled: true,
        pattern: "^[^\\s]+$",
        option_label: "Use '{value}' as a custom model ID",
      },
      placements: ["composer"],
      default_pinned: true,
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
      show_label: false,
      options: [{ value: "claude-a", label: "Claude A" }],
      placeholder: "Search models or enter a model ID",
      custom_value: {
        enabled: true,
        pattern: "^[^\\s]+$",
        option_label: "Use '{value}' as a custom model ID",
      },
      placements: ["composer"],
      default_pinned: true,
    });
  });

  it("requires ordinary fallback presentation outside rich UI", () => {
    const missingOuterIcon = normalizeConfigRichUiElement(
      modelElement({ icon: undefined }),
    );
    const nestedIcon = modelElement();
    (nestedIcon.rich_ui as Record<string, unknown>).icon = "cpu";

    expect(missingOuterIcon.value).toBeNull();
    expect(missingOuterIcon.diagnostics[0].message).toContain("outer icon");
    expect(
      normalizeConfigRichUiElement(nestedIcon).diagnostics[0].message,
    ).toContain("containing config element");
  });

  it("allows an empty custom-enabled dropdown without a text fallback", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({
        options: [],
        rich_ui: {
          kind: "dropdown",
          label: "Model",
          options: [],
          custom_value: {
            enabled: true,
            option_label: "Use '{value}'",
          },
          placements: ["composer"],
        },
      }),
    );

    expect(result.value?.rich_ui).toMatchObject({
      kind: "dropdown",
      options: [],
      custom_value: { enabled: true },
    });
  });

  it("does not inherit missing presentation fields from the config element", () => {
    const raw = modelElement();
    (raw.rich_ui as Record<string, unknown>).label = undefined;

    const result = normalizeConfigRichUiElement(raw);

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain("rich_ui.label");
  });

  it("requires custom entry on both the config and rich declarations", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({ custom_value: { enabled: false } }),
    );

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain(
      "containing config element",
    );
  });

  it("normalizes toggle options and resolves the current value", () => {
    const result = normalizeConfigRichUiElement({
      ui_type: "config",
      type: "checkbox",
      key: "enable_web_search",
      label: "Enable web search",
      icon: "globe",
      rich_ui: {
        kind: "toggle",
        label: "Web search",
        show_label: false,
        show_icon: false,
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
    });

    expect(result.diagnostics).toEqual([]);
    expect(result.value?.rich_ui).toMatchObject({
      kind: "toggle",
      show_label: false,
      show_icon: false,
    });
    expect(
      resolveConfigRichToggleOption(result.value!.rich_ui as any, true),
    ).toMatchObject({ value: true, tone: "success" });
    expect(resolveConfigRichUiMenuStateLabel(result.value!.rich_ui, true)).toBe(
      "On",
    );
  });

  it("uses the selected dropdown label as neutral menu state text", () => {
    const result = normalizeConfigRichUiElement(modelElement());

    expect(
      resolveConfigRichUiMenuStateLabel(result.value!.rich_ui, "claude-a"),
    ).toBe("Claude A");
    expect(
      resolveConfigRichUiMenuStateLabel(
        result.value!.rich_ui,
        "vendor/custom-model",
      ),
    ).toBe("vendor/custom-model");
  });

  it("rejects unsupported option tones", () => {
    const result = normalizeConfigRichUiElement(
      modelElement({
        rich_ui: {
          kind: "dropdown",
          label: "Model",
          placements: ["composer"],
          options: [
            { value: "claude-a", label: "Claude A", tone: "ultraviolet" },
          ],
        },
      }),
    );

    expect(result.value).toBeNull();
    expect(result.diagnostics[0].message).toContain("tone");
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
      label: "Future setting",
      icon: "sliders",
      rich_ui: { kind: "future_control", label: "Future" },
    });

    expect(result.value?.rich_ui).toEqual({
      kind: "future_control",
      label: "Future",
    });
  });
});

describe("config dropdown suggestions", () => {
  it("allows unrestricted custom values by default", () => {
    const normalized = normalizeConfigDropdownPresentation({
      ui_type: "config",
      type: "dropdown",
      key: "model",
      label: "Model",
      options: [{ value: "declared-model", label: "Declared model" }],
    });
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(normalized.diagnostics).toEqual([]);
    expect(normalized.value?.custom_value).toEqual({
      enabled: true,
      option_label: "Use '{value}'",
    });
    expect(engine.suggestions("vendor/custom model")).toEqual([
      {
        kind: "custom",
        value: "vendor/custom model",
        label: "Use 'vendor/custom model'",
      },
    ]);
  });

  it("allows dropdown authors to disable custom values explicitly", () => {
    const normalized = normalizeConfigDropdownPresentation({
      ui_type: "config",
      type: "dropdown",
      key: "model",
      label: "Model",
      options: [{ value: "declared-model", label: "Declared model" }],
      custom_value: { enabled: false },
    });
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.suggestions("vendor/custom-model")).toEqual([]);
  });

  it("keeps fixed-choice rich dropdowns closed to custom values", () => {
    const normalized = normalizeConfigRichUiElement({
      ui_type: "config",
      type: "select",
      key: "reasoning_effort",
      label: "Reasoning effort",
      icon: "activity",
      options: [{ value: "high", label: "High" }],
      rich_ui: {
        kind: "dropdown",
        label: "Reasoning effort",
        options: [{ value: "high", label: "High" }],
        placements: ["composer"],
      },
    });
    const richUi = normalized.value?.rich_ui;

    expect(normalized.diagnostics).toEqual([]);
    expect(richUi?.kind).toBe("dropdown");
    if (richUi?.kind !== "dropdown") {
      throw new Error("Expected a rich dropdown");
    }
    expect(richUi.custom_value).toBeUndefined();
    expect(createConfigDropdownSuggestionEngine(richUi).suggestions("max")).toEqual(
      [],
    );
  });

  it("filters declared options and appends a valid custom option", () => {
    const normalized = normalizeConfigDropdownPresentation(modelElement());
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.diagnostics).toEqual([]);
    expect(engine.suggestions("claude")).toEqual([
      {
        kind: "declared",
        value: "claude-a",
        label: "Claude A",
      },
      {
        kind: "custom",
        value: "claude",
        label: "Use 'claude' as a custom model ID",
      },
    ]);
  });

  it("suppresses the custom row for an exact declared value or invalid input", () => {
    const normalized = normalizeConfigDropdownPresentation(modelElement());
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.suggestions("claude-a")).toEqual([
      {
        kind: "declared",
        value: "claude-a",
        label: "Claude A",
      },
    ]);
    expect(engine.suggestions("not valid")).toEqual([]);
  });

  it("keeps declared options usable when the custom regex is invalid", () => {
    const normalized = normalizeConfigDropdownPresentation(
      modelElement({
        custom_value: {
          enabled: true,
          pattern: "[",
          option_label: "Use '{value}'",
        },
      }),
    );
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.diagnostics[0].code).toBe(
      "invalid_config_dropdown_custom_pattern",
    );
    expect(engine.suggestions("claude")).toEqual([
      {
        kind: "declared",
        value: "claude-a",
        label: "Claude A",
      },
    ]);
  });

  it("returns every declared option for an empty query", () => {
    const normalized = normalizeConfigDropdownPresentation(
      modelElement({
        options: [
          { value: "claude-a", label: "Claude A" },
          { value: "claude-b", label: "Claude B" },
        ],
      }),
    );
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.suggestions("")).toEqual([
      { kind: "declared", value: "claude-a", label: "Claude A" },
      { kind: "declared", value: "claude-b", label: "Claude B" },
    ]);
  });

  it("disables only custom entry when the label template is malformed", () => {
    const normalized = normalizeConfigDropdownPresentation(
      modelElement({
        custom_value: {
          enabled: true,
          option_label: "Use custom model",
        },
      }),
    );
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.diagnostics[0].code).toBe(
      "invalid_config_dropdown_custom_label",
    );
    expect(engine.suggestions("claude")).toEqual([
      { kind: "declared", value: "claude-a", label: "Claude A" },
    ]);
  });

  it("accepts any non-empty custom value when no pattern is declared", () => {
    const normalized = normalizeConfigDropdownPresentation(
      modelElement({
        custom_value: {
          enabled: true,
          option_label: "Use '{value}'",
        },
      }),
    );
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.suggestions("custom model")).toEqual([
      {
        kind: "custom",
        value: "custom model",
        label: "Use 'custom model'",
      },
    ]);
  });

  it("trims before exact matching and avoids a duplicate custom row", () => {
    const normalized = normalizeConfigDropdownPresentation(modelElement());
    const engine = createConfigDropdownSuggestionEngine(normalized.value!);

    expect(engine.suggestions("  claude-a  ")).toEqual([
      {
        kind: "declared",
        value: "claude-a",
        label: "Claude A",
      },
    ]);
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
