import type { ActionUiElement } from "../types/plugins";
import type { UiSchemaElement } from "../types/uiSchema";
import {
  normalizeSessionListActionElement,
  type SessionListActionElement,
  type SessionListRichUi,
} from "../sessions/sessionListContracts";
import type { SessionListOptionTone } from "../sessions/sessionListFilters";

export const CHAT_RICH_UI_PLACEMENTS = ["session_header", "composer"] as const;

export type ChatRichUiPlacement = (typeof CHAT_RICH_UI_PLACEMENTS)[number];

export interface RichUiDiagnostic {
  code: string;
  message: string;
  elementKey?: string;
  elementId?: string;
}

export interface RichUiNormalizationResult<T> {
  value: T | null;
  diagnostics: RichUiDiagnostic[];
}

export interface RichDropdownOption {
  value: string;
  label: string;
  icon?: string;
  tone?: SessionListOptionTone;
}

export interface RichToggleOption {
  value: boolean;
  label: string;
  icon?: string;
  tone?: SessionListOptionTone;
}

export interface ConfigCustomValue {
  enabled: boolean;
  pattern?: string;
  option_label?: string;
}

export interface ConfigDropdownPresentation {
  options: readonly RichDropdownOption[];
  placeholder?: string;
  custom_value?: ConfigCustomValue;
}

export interface ConfigDropdownSuggestion extends RichDropdownOption {
  kind: "declared" | "custom";
}

export interface ConfigDropdownSuggestionEngine {
  diagnostics: readonly RichUiDiagnostic[];
  suggestions(query: string): ConfigDropdownSuggestion[];
}

export interface ConfigRichUiBase {
  kind: string;
  label: string;
  icon?: string;
  placements: readonly string[];
  default_pinned?: boolean;
  show_label?: boolean;
}

export interface ConfigRichDropdownUi extends ConfigRichUiBase {
  kind: "dropdown";
  options: readonly RichDropdownOption[];
  placeholder?: string;
  custom_value?: ConfigCustomValue;
  description?: string;
}

export interface ConfigRichToggleUi extends ConfigRichUiBase {
  kind: "toggle";
  options: readonly RichToggleOption[];
  description?: string;
}

export interface UnknownConfigRichUi {
  kind: string;
  [key: string]: unknown;
}

export type ConfigRichUi =
  ConfigRichDropdownUi | ConfigRichToggleUi | UnknownConfigRichUi;

export interface ConfigRichUiElement extends UiSchemaElement {
  key: string;
  rich_ui: ConfigRichUi;
}

export interface ConfigRichUiControl {
  element: ConfigRichUiElement;
  richUi: ConfigRichUi;
}

export interface SessionActionRichUiElement extends ActionUiElement {
  ui_type: "session_action";
  rich_ui?: SessionListRichUi;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

const SEMANTIC_TONES = new Set<SessionListOptionTone>([
  "primary",
  "highlight",
  "warning",
  "success",
  "danger",
  "muted",
]);

function normalizePlacements(
  raw: unknown,
  elementKey: string,
): RichUiNormalizationResult<readonly string[]> {
  if (!Array.isArray(raw) || raw.length === 0) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message:
            "rich_ui.placements must contain at least one non-empty string.",
          elementKey,
        },
      ],
    };
  }

  const placements: string[] = [];
  const seen = new Set<string>();
  const diagnostics: RichUiDiagnostic[] = [];
  for (const placement of raw) {
    if (typeof placement !== "string" || !placement) {
      diagnostics.push({
        code: "invalid_config_rich_ui",
        message:
          "Ignoring a rich_ui.placements entry that is not a non-empty string.",
        elementKey,
      });
      continue;
    }
    if (seen.has(placement)) {
      diagnostics.push({
        code: "invalid_config_rich_ui",
        message: `Ignoring duplicate rich_ui.placements entry ${JSON.stringify(placement)}.`,
        elementKey,
      });
      continue;
    }
    seen.add(placement);
    placements.push(placement);
  }

  if (placements.length === 0) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message: "rich_ui.placements has no usable entries.",
          elementKey,
        },
      ],
    };
  }
  return { value: placements, diagnostics };
}

function normalizeRichDropdownOptions(
  raw: unknown,
  elementKey: string,
): RichUiNormalizationResult<readonly RichDropdownOption[]> {
  if (!Array.isArray(raw)) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message: "rich_ui.dropdown.options must be an array.",
          elementKey,
        },
      ],
    };
  }

  const options: RichDropdownOption[] = [];
  const values = new Set<string>();
  for (const rawOption of raw) {
    const option =
      typeof rawOption === "string"
        ? { value: rawOption, label: rawOption }
        : rawOption;
    if (
      !isRecord(option) ||
      typeof option.value !== "string" ||
      !option.value ||
      typeof option.label !== "string" ||
      !option.label
    ) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message:
              "Every rich dropdown option requires non-empty string value and label fields.",
            elementKey,
          },
        ],
      };
    }
    if (values.has(option.value)) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: `Rich dropdown option value ${JSON.stringify(option.value)} is duplicated.`,
            elementKey,
          },
        ],
      };
    }
    if (option.icon !== undefined && typeof option.icon !== "string") {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: "Rich dropdown option icons must be strings.",
            elementKey,
          },
        ],
      };
    }
    if (
      option.tone !== undefined &&
      !SEMANTIC_TONES.has(option.tone as SessionListOptionTone)
    ) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: "Rich dropdown option tone is not supported.",
            elementKey,
          },
        ],
      };
    }
    values.add(option.value);
    options.push({
      value: option.value,
      label: option.label,
      ...(typeof option.icon === "string" ? { icon: option.icon } : {}),
      ...(typeof option.tone === "string"
        ? { tone: option.tone as SessionListOptionTone }
        : {}),
    });
  }
  return { value: options, diagnostics: [] };
}

function normalizeRichToggleOptions(
  raw: unknown,
  elementKey: string,
): RichUiNormalizationResult<readonly RichToggleOption[]> {
  if (!Array.isArray(raw) || raw.length !== 2) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message:
            "rich_ui.toggle.options must contain exactly one false and one true option.",
          elementKey,
        },
      ],
    };
  }

  const options: RichToggleOption[] = [];
  const values = new Set<boolean>();
  for (const option of raw) {
    if (
      !isRecord(option) ||
      typeof option.value !== "boolean" ||
      typeof option.label !== "string" ||
      !option.label
    ) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message:
              "Every rich toggle option requires a boolean value and non-empty label.",
            elementKey,
          },
        ],
      };
    }
    if (values.has(option.value)) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message:
              "rich_ui.toggle.options must contain distinct false and true values.",
            elementKey,
          },
        ],
      };
    }
    if (option.icon !== undefined && typeof option.icon !== "string") {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: "Rich toggle option icons must be strings.",
            elementKey,
          },
        ],
      };
    }
    if (
      option.tone !== undefined &&
      !SEMANTIC_TONES.has(option.tone as SessionListOptionTone)
    ) {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: "Rich toggle option tone is not supported.",
            elementKey,
          },
        ],
      };
    }
    values.add(option.value);
    options.push({
      value: option.value,
      label: option.label,
      ...(typeof option.icon === "string" ? { icon: option.icon } : {}),
      ...(typeof option.tone === "string"
        ? { tone: option.tone as SessionListOptionTone }
        : {}),
    });
  }

  if (!values.has(false) || !values.has(true)) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message:
            "rich_ui.toggle.options must contain exactly one false and one true option.",
          elementKey,
        },
      ],
    };
  }
  return { value: options, diagnostics: [] };
}

function normalizeCustomValue(
  raw: unknown,
  elementKey: string,
  field: string,
): RichUiNormalizationResult<ConfigCustomValue | undefined> {
  if (raw === undefined) {
    return { value: undefined, diagnostics: [] };
  }
  if (!isRecord(raw) || typeof raw.enabled !== "boolean") {
    return {
      value: undefined,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message: `${field}.enabled must be a boolean.`,
          elementKey,
        },
      ],
    };
  }
  if (raw.pattern !== undefined && typeof raw.pattern !== "string") {
    return {
      value: undefined,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message: `${field}.pattern must be a string.`,
          elementKey,
        },
      ],
    };
  }
  if (raw.option_label !== undefined && typeof raw.option_label !== "string") {
    return {
      value: undefined,
      diagnostics: [
        {
          code: "invalid_config_rich_ui",
          message: `${field}.option_label must be a string.`,
          elementKey,
        },
      ],
    };
  }
  return {
    value: {
      enabled: raw.enabled,
      ...(typeof raw.pattern === "string" ? { pattern: raw.pattern } : {}),
      ...(typeof raw.option_label === "string"
        ? { option_label: raw.option_label }
        : {}),
    },
    diagnostics: [],
  };
}

export function normalizeConfigDropdownPresentation(
  raw: unknown,
): RichUiNormalizationResult<ConfigDropdownPresentation> {
  const elementKey =
    isRecord(raw) && typeof raw.key === "string" ? raw.key : undefined;
  if (!isRecord(raw)) {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_dropdown",
          message: "A config dropdown must be an object.",
          elementKey,
        },
      ],
    };
  }
  const options = normalizeRichDropdownOptions(
    raw.options ?? [],
    elementKey ?? "",
  );
  if (!options.value) {
    return { value: null, diagnostics: options.diagnostics };
  }
  if (raw.placeholder !== undefined && typeof raw.placeholder !== "string") {
    return {
      value: null,
      diagnostics: [
        {
          code: "invalid_config_dropdown",
          message: "dropdown.placeholder must be a string.",
          elementKey,
        },
      ],
    };
  }
  const customValue = normalizeCustomValue(
    raw.custom_value,
    elementKey ?? "",
    "dropdown.custom_value",
  );
  if (options.value.length === 0 && customValue.value?.enabled !== true) {
    return {
      value: null,
      diagnostics: [
        ...customValue.diagnostics,
        {
          code: "invalid_config_dropdown",
          message:
            "A dropdown requires declared options or custom_value.enabled.",
          elementKey,
        },
      ],
    };
  }
  return {
    value: {
      options: options.value,
      ...(typeof raw.placeholder === "string"
        ? { placeholder: raw.placeholder }
        : {}),
      ...(customValue.value ? { custom_value: customValue.value } : {}),
    },
    diagnostics: customValue.diagnostics,
  };
}

export function createConfigDropdownSuggestionEngine(
  presentation: ConfigDropdownPresentation,
): ConfigDropdownSuggestionEngine {
  const diagnostics: RichUiDiagnostic[] = [];
  const customValue = presentation.custom_value;
  let pattern: RegExp | null = null;
  let customEnabled = customValue?.enabled === true;

  if (customEnabled && customValue?.pattern) {
    try {
      pattern = new RegExp(`^(?:${customValue.pattern})$`);
    } catch {
      diagnostics.push({
        code: "invalid_config_dropdown_custom_pattern",
        message: "custom_value.pattern is not a valid ECMAScript regex.",
      });
      customEnabled = false;
    }
  }

  if (
    customEnabled &&
    (!customValue?.option_label ||
      !customValue.option_label.includes("{value}"))
  ) {
    diagnostics.push({
      code: "invalid_config_dropdown_custom_label",
      message: "custom_value.option_label must contain the {value} token.",
    });
    customEnabled = false;
  }

  return {
    diagnostics,
    suggestions(query: string): ConfigDropdownSuggestion[] {
      const candidate = String(query ?? "").trim();
      const normalizedQuery = candidate.toLocaleLowerCase();
      const declared = presentation.options
        .filter(
          (option) =>
            !normalizedQuery ||
            option.label.toLocaleLowerCase().includes(normalizedQuery) ||
            option.value.toLocaleLowerCase().includes(normalizedQuery),
        )
        .map((option) => ({ ...option, kind: "declared" as const }));
      if (
        !candidate ||
        !customEnabled ||
        presentation.options.some((option) => option.value === candidate) ||
        (pattern && !pattern.test(candidate))
      ) {
        return declared;
      }
      return [
        ...declared,
        {
          kind: "custom",
          value: candidate,
          label: customValue!.option_label!.split("{value}").join(candidate),
        },
      ];
    },
  };
}

export function resolveConfigRichToggleOption(
  richUi: ConfigRichToggleUi,
  value: unknown,
): RichToggleOption {
  const booleanValue = value === true;
  return (
    richUi.options.find((option) => option.value === booleanValue) ??
    richUi.options.find((option) => option.value === false) ??
    richUi.options[0]
  );
}

export function resolveConfigRichUiMenuStateLabel(
  richUi: ConfigRichDropdownUi | ConfigRichToggleUi,
  value: unknown,
): string | undefined {
  if (richUi.kind === "toggle") {
    return resolveConfigRichToggleOption(richUi, value).label;
  }
  if (richUi.kind === "dropdown") {
    const normalizedValue =
      value === undefined || value === null ? "" : String(value);
    if (!normalizedValue) {
      return undefined;
    }
    return (
      richUi.options.find((option) => option.value === normalizedValue)
        ?.label ?? normalizedValue
    );
  }
  return undefined;
}

export function normalizeConfigRichUiElement(
  raw: unknown,
): RichUiNormalizationResult<ConfigRichUiElement> {
  const elementKey =
    isRecord(raw) && typeof raw.key === "string" ? raw.key : undefined;
  const fail = (
    message: string,
  ): RichUiNormalizationResult<ConfigRichUiElement> => ({
    value: null,
    diagnostics: [
      {
        code: "invalid_config_rich_ui",
        message,
        elementKey,
      },
    ],
  });

  if (!isRecord(raw)) {
    return fail("A rich config element must be an object.");
  }
  if (
    raw.ui_type !== undefined &&
    raw.ui_type !== null &&
    raw.ui_type !== "" &&
    raw.ui_type !== "config"
  ) {
    return fail(
      'A rich config element must use ui_type "config" or omit ui_type.',
    );
  }
  if (typeof raw.key !== "string" || !raw.key) {
    return fail("A rich config element requires a non-empty key.");
  }
  if (
    !isRecord(raw.rich_ui) ||
    typeof raw.rich_ui.kind !== "string" ||
    !raw.rich_ui.kind
  ) {
    return fail("rich_ui.kind must be a non-empty string.");
  }

  if (raw.rich_ui.kind !== "dropdown" && raw.rich_ui.kind !== "toggle") {
    return {
      value: {
        ...(raw as UiSchemaElement),
        key: raw.key,
        rich_ui: raw.rich_ui as UnknownConfigRichUi,
      },
      diagnostics: [],
    };
  }

  const rich = raw.rich_ui;
  if (typeof rich.label !== "string" || !rich.label) {
    return fail("rich_ui.label must be a non-empty string.");
  }
  if (rich.icon !== undefined && typeof rich.icon !== "string") {
    return fail("rich_ui.icon must be a string.");
  }
  if (
    rich.default_pinned !== undefined &&
    typeof rich.default_pinned !== "boolean"
  ) {
    return fail("rich_ui.default_pinned must be a boolean.");
  }
  if (rich.show_label !== undefined && typeof rich.show_label !== "boolean") {
    return fail("rich_ui.show_label must be a boolean.");
  }
  if (rich.description !== undefined && typeof rich.description !== "string") {
    return fail("rich_ui.description must be a string.");
  }

  const placements = normalizePlacements(rich.placements, raw.key);
  if (!placements.value) {
    return { value: null, diagnostics: placements.diagnostics };
  }
  const common = {
    label: rich.label,
    placements: placements.value,
    ...(typeof rich.icon === "string" ? { icon: rich.icon } : {}),
    ...(typeof rich.default_pinned === "boolean"
      ? { default_pinned: rich.default_pinned }
      : {}),
    ...(typeof rich.show_label === "boolean"
      ? { show_label: rich.show_label }
      : {}),
    ...(typeof rich.description === "string"
      ? { description: rich.description }
      : {}),
  };

  let normalizedRich: ConfigRichDropdownUi | ConfigRichToggleUi;
  let diagnostics = [...placements.diagnostics];
  if (rich.kind === "toggle") {
    if (raw.type !== "checkbox" && raw.type !== "boolean") {
      return fail(
        "A rich config toggle requires a checkbox or boolean config element.",
      );
    }
    const options = normalizeRichToggleOptions(rich.options, raw.key);
    if (!options.value) {
      return { value: null, diagnostics: options.diagnostics };
    }
    normalizedRich = {
      kind: "toggle",
      ...common,
      options: options.value,
    };
  } else {
    const presentation = normalizeConfigDropdownPresentation({
      key: raw.key,
      options: rich.options,
      placeholder: rich.placeholder,
      custom_value: rich.custom_value,
    });
    if (!presentation.value) {
      return { value: null, diagnostics: presentation.diagnostics };
    }
    diagnostics = [...diagnostics, ...presentation.diagnostics];
    if (presentation.value.custom_value?.enabled === true) {
      const outerCustom = normalizeCustomValue(
        raw.custom_value,
        raw.key,
        "dropdown.custom_value",
      );
      diagnostics.push(...outerCustom.diagnostics);
      if (outerCustom.value?.enabled !== true) {
        return fail(
          "A rich dropdown with custom_value.enabled requires custom_value.enabled on the containing config element.",
        );
      }
      if (raw.type !== "dropdown") {
        return fail(
          "A custom-enabled rich dropdown requires a dropdown config element.",
        );
      }
    }
    normalizedRich = {
      kind: "dropdown",
      ...common,
      options: presentation.value.options,
      ...(presentation.value.placeholder
        ? { placeholder: presentation.value.placeholder }
        : {}),
      ...(presentation.value.custom_value
        ? { custom_value: presentation.value.custom_value }
        : {}),
    };
  }

  return {
    value: {
      ...(raw as UiSchemaElement),
      key: raw.key,
      rich_ui: normalizedRich,
    },
    diagnostics,
  };
}

export function selectConfigRichUiControls(
  elements: readonly UiSchemaElement[],
  placement?: ChatRichUiPlacement,
): {
  controls: ConfigRichUiControl[];
  diagnostics: RichUiDiagnostic[];
} {
  const controls: ConfigRichUiControl[] = [];
  const diagnostics: RichUiDiagnostic[] = [];
  for (const element of elements) {
    if (!isRecord(element) || element.rich_ui === undefined) {
      continue;
    }
    const normalized = normalizeConfigRichUiElement(element);
    diagnostics.push(...normalized.diagnostics);
    if (!normalized.value) {
      continue;
    }
    const richUi = normalized.value.rich_ui;
    if (
      placement &&
      (!Array.isArray((richUi as ConfigRichUiBase).placements) ||
        !(richUi as ConfigRichUiBase).placements.includes(placement))
    ) {
      continue;
    }
    controls.push({ element: normalized.value, richUi });
  }
  return { controls, diagnostics };
}

export function getDefaultPinnedConfigRichUiKeys(
  controls: readonly ConfigRichUiControl[],
): string[] {
  return controls
    .filter((control) => control.richUi.default_pinned === true)
    .map((control) => control.element.key);
}

export function normalizeSessionActionRichUiElement(
  raw: unknown,
): RichUiNormalizationResult<SessionActionRichUiElement> {
  const elementId =
    isRecord(raw) && typeof raw.id === "string" ? raw.id : undefined;
  const fail = (
    message: string,
  ): RichUiNormalizationResult<SessionActionRichUiElement> => ({
    value: null,
    diagnostics: [
      {
        code: "invalid_session_action",
        message,
        elementId,
      },
    ],
  });

  if (!isRecord(raw) || raw.ui_type !== "session_action") {
    return fail("session_action must be an object with the matching ui_type.");
  }

  const normalized = normalizeSessionListActionElement({
    ...raw,
    ui_type: "session_list_action",
    dialog: raw.dialog ?? { kind: "none" },
  });
  const diagnostics = normalized.diagnostics.map((diagnostic) => ({
    ...diagnostic,
    code:
      diagnostic.code === "invalid_session_list_rich_ui"
        ? "invalid_session_action_rich_ui"
        : diagnostic.code === "invalid_session_list_action"
          ? "invalid_session_action"
          : diagnostic.code,
  }));
  if (!normalized.value) {
    return { value: null, diagnostics };
  }

  const value: SessionActionRichUiElement = {
    ...(normalized.value as SessionListActionElement),
    ui_type: "session_action",
  };
  return { value, diagnostics };
}

export function getSessionActionRichUiPlacements(
  element: SessionActionRichUiElement,
): readonly string[] {
  const placements = element.rich_ui?.placements;
  return Array.isArray(placements) && placements.length > 0
    ? placements
    : ["session_header"];
}

export function isSessionActionPlacedAt(
  element: SessionActionRichUiElement,
  placement: ChatRichUiPlacement,
): boolean {
  return getSessionActionRichUiPlacements(element).includes(placement);
}

export function normalizeSessionActionRichUiElements(
  elements: readonly ActionUiElement[],
): {
  elements: SessionActionRichUiElement[];
  diagnostics: RichUiDiagnostic[];
} {
  const normalizedElements: SessionActionRichUiElement[] = [];
  const diagnostics: RichUiDiagnostic[] = [];
  for (const element of elements) {
    const normalized = normalizeSessionActionRichUiElement(element);
    diagnostics.push(...normalized.diagnostics);
    if (normalized.value) {
      normalizedElements.push(normalized.value);
    }
  }
  return { elements: normalizedElements, diagnostics };
}
