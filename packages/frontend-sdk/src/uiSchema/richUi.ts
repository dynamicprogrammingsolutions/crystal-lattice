import type { ActionUiElement } from "../types/plugins";
import type { UiSchemaElement } from "../types/uiSchema";
import {
  normalizeSessionListActionElement,
  type SessionListActionElement,
  type SessionListRichUi,
} from "../sessions/sessionListContracts";

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
  tone?: string;
}

export interface ConfigRichUiBase {
  kind: string;
  label: string;
  icon?: string;
  placements: readonly string[];
  default_pinned?: boolean;
}

export interface ConfigRichDropdownUi extends ConfigRichUiBase {
  kind: "dropdown";
  options: readonly RichDropdownOption[];
  allow_custom_value?: boolean;
  custom_value_label?: string;
  custom_value_placeholder?: string;
  description?: string;
}

export interface UnknownConfigRichUi {
  kind: string;
  [key: string]: unknown;
}

export type ConfigRichUi = ConfigRichDropdownUi | UnknownConfigRichUi;

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
    if (option.tone !== undefined && typeof option.tone !== "string") {
      return {
        value: null,
        diagnostics: [
          {
            code: "invalid_config_rich_ui",
            message: "Rich dropdown option tones must be strings.",
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
      ...(typeof option.tone === "string" ? { tone: option.tone } : {}),
    });
  }
  return { value: options, diagnostics: [] };
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

  if (raw.rich_ui.kind !== "dropdown") {
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
    return fail("rich_ui.dropdown.label must be a non-empty string.");
  }
  if (rich.icon !== undefined && typeof rich.icon !== "string") {
    return fail("rich_ui.dropdown.icon must be a string.");
  }
  if (
    rich.default_pinned !== undefined &&
    typeof rich.default_pinned !== "boolean"
  ) {
    return fail("rich_ui.dropdown.default_pinned must be a boolean.");
  }
  if (
    rich.allow_custom_value !== undefined &&
    typeof rich.allow_custom_value !== "boolean"
  ) {
    return fail("rich_ui.dropdown.allow_custom_value must be a boolean.");
  }
  if (
    rich.custom_value_label !== undefined &&
    typeof rich.custom_value_label !== "string"
  ) {
    return fail("rich_ui.dropdown.custom_value_label must be a string.");
  }
  if (
    rich.custom_value_placeholder !== undefined &&
    typeof rich.custom_value_placeholder !== "string"
  ) {
    return fail("rich_ui.dropdown.custom_value_placeholder must be a string.");
  }
  if (rich.description !== undefined && typeof rich.description !== "string") {
    return fail("rich_ui.dropdown.description must be a string.");
  }

  const placements = normalizePlacements(rich.placements, raw.key);
  if (!placements.value) {
    return { value: null, diagnostics: placements.diagnostics };
  }
  const options = normalizeRichDropdownOptions(rich.options, raw.key);
  if (!options.value) {
    return { value: null, diagnostics: options.diagnostics };
  }

  const allowCustom = rich.allow_custom_value === true;
  if (allowCustom && raw.allow_custom_value !== true) {
    return fail(
      "A rich dropdown with allow_custom_value requires allow_custom_value on the containing config element.",
    );
  }
  if (
    allowCustom &&
    raw.type !== "dropdown" &&
    raw.type !== "text" &&
    raw.type !== "string"
  ) {
    return fail(
      "Custom rich dropdown values require a string-valued config element.",
    );
  }
  if (options.value.length === 0 && !allowCustom) {
    return fail("A rich dropdown requires options or allow_custom_value.");
  }

  const normalizedRich: ConfigRichDropdownUi = {
    kind: "dropdown",
    label: rich.label,
    placements: placements.value,
    options: options.value,
    ...(typeof rich.icon === "string" ? { icon: rich.icon } : {}),
    ...(typeof rich.default_pinned === "boolean"
      ? { default_pinned: rich.default_pinned }
      : {}),
    ...(allowCustom ? { allow_custom_value: true } : {}),
    ...(typeof rich.custom_value_label === "string"
      ? { custom_value_label: rich.custom_value_label }
      : {}),
    ...(typeof rich.custom_value_placeholder === "string"
      ? { custom_value_placeholder: rich.custom_value_placeholder }
      : {}),
    ...(typeof rich.description === "string"
      ? { description: rich.description }
      : {}),
  };

  return {
    value: {
      ...(raw as UiSchemaElement),
      key: raw.key,
      rich_ui: normalizedRich,
    },
    diagnostics: placements.diagnostics,
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
