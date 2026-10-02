import type { ActionUiElement, SessionListFieldElement } from '../types/plugins';
import type {
  SessionListOption,
  SessionListOptionTone,
  SessionListOptionValue,
} from './sessionListFilters';

export interface SessionListContractDiagnostic {
  code: string;
  message: string;
  elementId?: string;
  details?: Record<string, unknown>;
}

export interface SessionListPathResult {
  found: boolean;
  value?: unknown;
}

export type ActionDialogKind = 'none' | 'confirm' | 'form';

export interface ActionDialogInput {
  name: string;
  type?: string;
  label?: string;
  placeholder?: string;
  default?: unknown;
  required?: boolean;
  description?: string;
  options?: unknown;
  prefill_from?: string;
  submit_empty?: boolean;
}

export interface ActionDialog {
  kind: ActionDialogKind;
  title?: string;
  message?: string;
  inputs?: ActionDialogInput[];
  [key: string]: unknown;
}

export type SemanticTone = SessionListOptionTone;

export const SESSION_LIST_RICH_ACTION_PLACEMENTS = [
  'actions_bar',
  'header_leading',
  'header_trailing',
] as const;

export type SessionListRichActionPlacement =
  (typeof SESSION_LIST_RICH_ACTION_PLACEMENTS)[number];

export interface SessionListRichUiBase {
  kind: string;
  value_path: string;
  missing_value?: unknown;
  default_pinned?: boolean;
  /**
   * Ordered display locations. Unknown strings remain transportable so a
   * future frontend can support them; current frontends ignore them.
   */
  placements?: readonly string[];
}

export interface SessionListRichAppearance {
  tone: SemanticTone;
}

export interface SessionListToggleRichUi extends SessionListRichUiBase {
  kind: 'toggle';
  active_value: string | number | boolean;
  appearance: {
    active: SessionListRichAppearance;
    inactive: SessionListRichAppearance;
  };
}

export interface SessionListListRichUi extends SessionListRichUiBase {
  kind: 'list';
  input_name: string;
  options: readonly SessionListOption[];
}

export interface SessionListButtonRichUi {
  kind: 'button';
  placements?: readonly string[];
  anchor_key?: string;
  position?: 'after';
  tone?: SemanticTone;
  default_pinned?: boolean;
}

/**
 * Unknown rich kinds are intentionally transportable. A frontend that does
 * not explicitly support the kind uses the ordinary dialog presentation.
 */
export interface UnknownSessionListRichUi {
  kind: string;
  [key: string]: unknown;
}

export type SessionListRichUi =
  | SessionListToggleRichUi
  | SessionListListRichUi
  | SessionListButtonRichUi
  | UnknownSessionListRichUi;

export interface SessionListActionElement extends ActionUiElement {
  ui_type: 'session_list_action';
  dialog: ActionDialog;
  rich_ui?: SessionListRichUi;
}

export interface SessionListOrderSpec {
  key: string;
  direction: 'asc' | 'desc';
  fallback?: unknown;
  priority: number;
}

export interface NormalizationResult<T> {
  value: T | null;
  diagnostics: SessionListContractDiagnostic[];
}

export interface ActionDialogPrefillContext {
  session?: unknown;
  message?: unknown;
}

export type SessionListActionPresentation =
  | { mode: 'dialog'; dialog: ActionDialog }
  | { mode: 'rich'; richUi: SessionListRichUi };

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

const SEMANTIC_TONES = new Set<SemanticTone>([
  'primary',
  'highlight',
  'warning',
  'success',
  'danger',
  'muted',
]);

function normalizeRichPlacements(
  raw: unknown,
  elementId: string,
): { placements?: readonly string[]; diagnostics: SessionListContractDiagnostic[] } {
  if (raw === undefined) {
    return { diagnostics: [] };
  }
  if (!Array.isArray(raw)) {
    return {
      diagnostics: [{
        code: 'invalid_session_list_rich_ui',
        message: 'rich_ui.placements must be an array of non-empty strings.',
        elementId,
      }],
    };
  }

  const placements: string[] = [];
  const seen = new Set<string>();
  const diagnostics: SessionListContractDiagnostic[] = [];
  for (const placement of raw) {
    if (typeof placement !== 'string' || !placement) {
      diagnostics.push({
        code: 'invalid_session_list_rich_ui',
        message: 'Ignoring a rich_ui.placements entry that is not a non-empty string.',
        elementId,
      });
      continue;
    }
    if (seen.has(placement)) {
      diagnostics.push({
        code: 'invalid_session_list_rich_ui',
        message: `Ignoring duplicate rich_ui.placements entry ${JSON.stringify(placement)}.`,
        elementId,
      });
      continue;
    }
    seen.add(placement);
    placements.push(placement);
  }
  if (placements.length === 0) {
    diagnostics.push({
      code: 'invalid_session_list_rich_ui',
      message: 'rich_ui.placements has no usable entries; using the default actions_bar.',
      elementId,
    });
    return { diagnostics };
  }
  return { placements, diagnostics };
}

function isOptionValue(value: unknown): value is SessionListOptionValue {
  return typeof value === 'string' || typeof value === 'boolean';
}

function typedValueKey(value: unknown): string {
  return `${typeof value}:${String(value)}`;
}

function normalizeRichOptions(
  raw: unknown,
  elementId: string,
): NormalizationResult<readonly SessionListOption[]> {
  if (!Array.isArray(raw) || raw.length === 0) {
    return {
      value: null,
      diagnostics: [{
        code: 'invalid_session_list_rich_ui',
        message: 'rich_ui.list.options must be a non-empty list.',
        elementId,
      }],
    };
  }

  const options: SessionListOption[] = [];
  const values = new Set<string>();
  for (const option of raw) {
    if (!isRecord(option) || !isOptionValue(option.value)) {
      return {
        value: null,
        diagnostics: [{
          code: 'invalid_session_list_rich_ui',
          message: 'Every rich_ui.list option requires a string or boolean value.',
          elementId,
        }],
      };
    }
    if (typeof option.label !== 'string' || !option.label) {
      return {
        value: null,
        diagnostics: [{
          code: 'invalid_session_list_rich_ui',
          message: 'Every rich_ui.list option requires a non-empty label.',
          elementId,
        }],
      };
    }
    if (option.icon !== undefined && typeof option.icon !== 'string') {
      return {
        value: null,
        diagnostics: [{
          code: 'invalid_session_list_rich_ui',
          message: 'rich_ui.list option icons must be strings.',
          elementId,
        }],
      };
    }
    if (
      option.tone !== undefined &&
      (!SEMANTIC_TONES.has(option.tone as SemanticTone))
    ) {
      return {
        value: null,
        diagnostics: [{
          code: 'invalid_session_list_rich_ui',
          message: 'rich_ui.list option tone is not supported.',
          elementId,
        }],
      };
    }
    const key = typedValueKey(option.value);
    if (values.has(key)) {
      return {
        value: null,
        diagnostics: [{
          code: 'invalid_session_list_rich_ui',
          message: 'rich_ui.list option values must be unique by type and value.',
          elementId,
        }],
      };
    }
    values.add(key);
    options.push({
      value: option.value,
      label: option.label,
      ...(typeof option.icon === 'string' ? { icon: option.icon } : {}),
      ...(typeof option.tone === 'string'
        ? { tone: option.tone as SemanticTone }
        : {}),
    });
  }
  return { value: options, diagnostics: [] };
}

function normalizeRichAppearance(
  raw: unknown,
  field: 'active' | 'inactive',
  elementId: string,
): NormalizationResult<SessionListRichAppearance> {
  if (
    !isRecord(raw) ||
    !isRecord(raw[field]) ||
    !SEMANTIC_TONES.has((raw[field] as Record<string, unknown>).tone as SemanticTone)
  ) {
    return {
      value: null,
      diagnostics: [{
        code: 'invalid_session_list_rich_ui',
        message: `rich_ui.toggle.appearance.${field}.tone must be a supported semantic tone.`,
        elementId,
      }],
    };
  }
  return {
    value: {
      tone: (raw[field] as Record<string, unknown>).tone as SemanticTone,
    },
    diagnostics: [],
  };
}

function normalizeRichUi(
  raw: unknown,
  elementId: string,
): NormalizationResult<SessionListRichUi> {
  const fail = (message: string): NormalizationResult<SessionListRichUi> => ({
    value: null,
    diagnostics: [{
      code: 'invalid_session_list_rich_ui',
      message,
      elementId,
    }],
  });

  if (!isRecord(raw) || typeof raw.kind !== 'string' || !raw.kind) {
    return fail('Ignoring malformed rich_ui while preserving the ordinary action.');
  }

  if (raw.kind === 'button') {
    const placements = normalizeRichPlacements(raw.placements, elementId);
    if (
      raw.anchor_key !== undefined &&
      (typeof raw.anchor_key !== 'string' || !raw.anchor_key)
    ) {
      return fail('rich_ui.button.anchor_key must be a non-empty string.');
    }
    if (raw.position !== undefined && raw.position !== 'after') {
      return fail("rich_ui.button.position currently supports only 'after'.");
    }
    if (
      raw.tone !== undefined &&
      (typeof raw.tone !== 'string' || !SEMANTIC_TONES.has(raw.tone as SemanticTone))
    ) {
      return fail('rich_ui.button.tone must be a supported semantic tone.');
    }
    if (
      raw.default_pinned !== undefined &&
      typeof raw.default_pinned !== 'boolean'
    ) {
      return fail('rich_ui.button.default_pinned must be a boolean.');
    }
    return {
      value: {
        kind: 'button',
        ...(placements.placements !== undefined
          ? { placements: placements.placements }
          : {}),
        ...(typeof raw.anchor_key === 'string'
          ? { anchor_key: raw.anchor_key }
          : {}),
        ...(raw.position === 'after' ? { position: 'after' as const } : {}),
        ...(typeof raw.tone === 'string'
          ? { tone: raw.tone as SemanticTone }
          : {}),
        ...(typeof raw.default_pinned === 'boolean'
          ? { default_pinned: raw.default_pinned }
          : {}),
      },
      diagnostics: placements.diagnostics,
    };
  }

  if (raw.kind !== 'toggle' && raw.kind !== 'list') {
    return { value: raw as UnknownSessionListRichUi, diagnostics: [] };
  }

  if (typeof raw.value_path !== 'string' || !raw.value_path) {
    return fail('rich_ui.value_path must be a non-empty dotted path.');
  }
  if (
    raw.default_pinned !== undefined &&
    typeof raw.default_pinned !== 'boolean'
  ) {
    return fail('rich_ui.default_pinned must be a boolean.');
  }
  const placements = normalizeRichPlacements(raw.placements, elementId);
  const withPlacements =
    placements.placements !== undefined
      ? { placements: placements.placements }
      : {};

  if (raw.kind === 'toggle') {
    if (
      typeof raw.active_value !== 'string' &&
      typeof raw.active_value !== 'number' &&
      typeof raw.active_value !== 'boolean'
    ) {
      return fail('rich_ui.toggle.active_value must be a string, number, or boolean.');
    }
    const active = normalizeRichAppearance(raw.appearance, 'active', elementId);
    if (!active.value) {
      return { value: null, diagnostics: active.diagnostics };
    }
    const inactive = normalizeRichAppearance(raw.appearance, 'inactive', elementId);
    if (!inactive.value) {
      return { value: null, diagnostics: inactive.diagnostics };
    }
    return {
      value: {
        kind: 'toggle',
        value_path: raw.value_path,
        ...(Object.prototype.hasOwnProperty.call(raw, 'missing_value')
          ? { missing_value: raw.missing_value }
          : {}),
        ...(typeof raw.default_pinned === 'boolean'
          ? { default_pinned: raw.default_pinned }
          : {}),
        ...withPlacements,
        active_value: raw.active_value,
        appearance: {
          active: active.value,
          inactive: inactive.value,
        },
      },
      diagnostics: placements.diagnostics,
    };
  }

  if (typeof raw.input_name !== 'string' || !raw.input_name) {
    return fail('rich_ui.list.input_name must be a non-empty string.');
  }
  const options = normalizeRichOptions(raw.options, elementId);
  if (!options.value) {
    return { value: null, diagnostics: options.diagnostics };
  }
  return {
    value: {
      kind: 'list',
      value_path: raw.value_path,
      ...(Object.prototype.hasOwnProperty.call(raw, 'missing_value')
        ? { missing_value: raw.missing_value }
        : {}),
      ...(typeof raw.default_pinned === 'boolean'
        ? { default_pinned: raw.default_pinned }
        : {}),
      ...withPlacements,
      input_name: raw.input_name,
      options: options.value,
    },
    diagnostics: placements.diagnostics,
  };
}

export function resolveSessionListPath(root: unknown, path: string): SessionListPathResult {
  if (typeof path !== 'string' || !path) {
    return { found: false };
  }

  let current: unknown = root;
  for (const part of path.split('.')) {
    if (Array.isArray(current)) {
      const index = Number(part);
      if (!Number.isInteger(index) || index < 0 || index >= current.length) {
        return { found: false };
      }
      current = current[index];
      continue;
    }
    if (isRecord(current)) {
      if (!Object.prototype.hasOwnProperty.call(current, part)) {
        return { found: false };
      }
      current = current[part];
      continue;
    }
    return { found: false };
  }
  return { found: true, value: current };
}

export function normalizeSessionListFieldElement(
  raw: unknown,
): NormalizationResult<SessionListFieldElement> {
  const diagnostics: SessionListContractDiagnostic[] = [];
  const elementId = isRecord(raw) && typeof raw.id === 'string' ? raw.id : undefined;
  const fail = (message: string): NormalizationResult<SessionListFieldElement> => ({
    value: null,
    diagnostics: [
      {
        code: 'invalid_session_list_field',
        message,
        elementId,
      },
    ],
  });

  if (!isRecord(raw) || raw.ui_type !== 'session_list_field') {
    return fail('session_list_field must be an object with the matching ui_type.');
  }
  if (typeof raw.id !== 'string' || !raw.id) {
    return fail('session_list_field.id must be a non-empty string.');
  }
  if (raw.role !== 'title' && raw.role !== 'subtitle' && raw.role !== 'meta') {
    return fail('session_list_field.role must be title, subtitle, or meta.');
  }
  if (typeof raw.data !== 'string' || !raw.data) {
    return fail('session_list_field.data must be a non-empty dotted path.');
  }
  if (raw.template !== undefined && typeof raw.template !== 'string') {
    return fail('session_list_field.template must be a string.');
  }
  if (
    raw.order !== undefined &&
    (typeof raw.order !== 'number' || !Number.isFinite(raw.order))
  ) {
    return fail('session_list_field.order must be a finite number.');
  }
  if (raw.metadata !== undefined && !isRecord(raw.metadata)) {
    return fail('session_list_field.metadata must be an object.');
  }

  return {
    value: {
      ...(raw as SessionListFieldElement),
      ui_type: 'session_list_field',
      id: raw.id,
      role: raw.role,
      data: raw.data,
      template: typeof raw.template === 'string' ? raw.template : '{{data}}',
      order: typeof raw.order === 'number' ? raw.order : 0,
    },
    diagnostics,
  };
}

export function normalizeSessionListOrderSpec(
  raw: unknown,
): NormalizationResult<SessionListOrderSpec> {
  const fail = (message: string): NormalizationResult<SessionListOrderSpec> => ({
    value: null,
    diagnostics: [
      {
        code: 'invalid_session_list_order_spec',
        message,
      },
    ],
  });

  if (!isRecord(raw)) {
    return fail('Session-list order specification must be an object.');
  }
  if (typeof raw.key !== 'string' || !raw.key) {
    return fail('Session-list order key must be a non-empty dotted path.');
  }
  if (raw.direction !== 'asc' && raw.direction !== 'desc') {
    return fail('Session-list order direction must be asc or desc.');
  }
  const priority = raw.priority === undefined ? 100 : raw.priority;
  if (typeof priority !== 'number' || !Number.isInteger(priority)) {
    return fail('Session-list order priority must be an integer.');
  }

  const value: SessionListOrderSpec = {
    key: raw.key,
    direction: raw.direction,
    priority,
  };
  if (Object.prototype.hasOwnProperty.call(raw, 'fallback')) {
    value.fallback = raw.fallback;
  }
  return { value, diagnostics: [] };
}

export function formatSessionListFieldValue(
  field: SessionListFieldElement,
  rawValue: unknown,
): unknown {
  const metadata = isRecord(field.metadata) ? field.metadata : {};
  if (metadata.format !== 'datetime') {
    return rawValue;
  }

  let date: Date | null = null;
  if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
    date = new Date(rawValue * 1000);
  } else if (typeof rawValue === 'string' && rawValue) {
    const parsed = new Date(rawValue);
    if (Number.isFinite(parsed.getTime())) {
      date = parsed;
    }
  }
  if (!date || !Number.isFinite(date.getTime())) {
    return rawValue;
  }
  return date.toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function normalizeDialog(
  raw: unknown,
  elementId: string,
): NormalizationResult<ActionDialog> {
  if (raw === undefined || raw === null) {
    return { value: { kind: 'none' }, diagnostics: [] };
  }
  if (!isRecord(raw)) {
    return {
      value: null,
      diagnostics: [
        {
          code: 'invalid_session_list_action',
          message: 'session_list_action.dialog must be an object.',
          elementId,
        },
      ],
    };
  }
  if (raw.kind !== 'none' && raw.kind !== 'confirm' && raw.kind !== 'form') {
    return {
      value: null,
      diagnostics: [
        {
          code: 'invalid_session_list_action',
          message: 'session_list_action.dialog.kind must be none, confirm, or form.',
          elementId,
        },
      ],
    };
  }
  if (raw.title !== undefined && typeof raw.title !== 'string') {
    return {
      value: null,
      diagnostics: [
        {
          code: 'invalid_session_list_action',
          message: 'session_list_action.dialog.title must be a string.',
          elementId,
        },
      ],
    };
  }
  if (raw.message !== undefined && typeof raw.message !== 'string') {
    return {
      value: null,
      diagnostics: [
        {
          code: 'invalid_session_list_action',
          message: 'session_list_action.dialog.message must be a string.',
          elementId,
        },
      ],
    };
  }

  const diagnostics: SessionListContractDiagnostic[] = [];
  const dialog: ActionDialog = {
    ...raw,
    kind: raw.kind,
  };
  if (raw.kind === 'form') {
    if (raw.inputs !== undefined && !Array.isArray(raw.inputs)) {
      return {
        value: null,
        diagnostics: [
          {
            code: 'invalid_session_list_action',
            message: 'A form dialog inputs value must be an array.',
            elementId,
          },
        ],
      };
    }
    const inputs: ActionDialogInput[] = [];
    for (const input of Array.isArray(raw.inputs) ? raw.inputs : []) {
      if (!isRecord(input) || typeof input.name !== 'string' || !input.name) {
        diagnostics.push({
          code: 'invalid_session_list_dialog_input',
          message: 'Ignoring a form input without a non-empty name.',
          elementId,
        });
        continue;
      }
      inputs.push({
        ...input,
        name: input.name,
      });
    }
    dialog.inputs = inputs;
  } else {
    delete dialog.inputs;
  }
  return { value: dialog, diagnostics };
}

export function normalizeSessionListActionElement(
  raw: unknown,
): NormalizationResult<SessionListActionElement> {
  const elementId = isRecord(raw) && typeof raw.id === 'string' ? raw.id : undefined;
  const fail = (message: string): NormalizationResult<SessionListActionElement> => ({
    value: null,
    diagnostics: [
      {
        code: 'invalid_session_list_action',
        message,
        elementId,
      },
    ],
  });

  if (!isRecord(raw) || raw.ui_type !== 'session_list_action') {
    return fail('session_list_action must be an object with the matching ui_type.');
  }
  if (typeof raw.plugin !== 'string' || !raw.plugin) {
    return fail('session_list_action.plugin must be a non-empty string.');
  }
  if (typeof raw.id !== 'string' || !raw.id) {
    return fail('session_list_action.id must be a non-empty string.');
  }
  if (typeof raw.label !== 'string' || !raw.label) {
    return fail('session_list_action.label must be a non-empty string.');
  }
  if (typeof raw.action_id !== 'string' || !raw.action_id) {
    return fail('session_list_action.action_id must be a non-empty string.');
  }
  if (
    raw.order !== undefined &&
    (typeof raw.order !== 'number' || !Number.isFinite(raw.order))
  ) {
    return fail('session_list_action.order must be a finite number.');
  }
  if (raw.fixed_params !== undefined && !isRecord(raw.fixed_params)) {
    return fail('session_list_action.fixed_params must be an object.');
  }
  if (raw.param_map !== undefined && !isRecord(raw.param_map)) {
    return fail('session_list_action.param_map must be an object.');
  }
  if (
    isRecord(raw.param_map) &&
    Object.values(raw.param_map).some((source) => typeof source !== 'string')
  ) {
    return fail('Every session_list_action.param_map value must be a string.');
  }

  const dialogResult = normalizeDialog(raw.dialog, raw.id);
  if (!dialogResult.value) {
    return {
      value: null,
      diagnostics: dialogResult.diagnostics,
    };
  }

  const diagnostics = [...dialogResult.diagnostics];
  let richUi: SessionListRichUi | undefined;
  if (raw.rich_ui !== undefined) {
    const richResult = normalizeRichUi(raw.rich_ui, raw.id);
    diagnostics.push(...richResult.diagnostics);
    richUi = richResult.value ?? undefined;
  }

  const value: SessionListActionElement = {
    ...(raw as ActionUiElement),
    ui_type: 'session_list_action',
    plugin: raw.plugin,
    id: raw.id,
    label: raw.label,
    action_id: raw.action_id,
    dialog: dialogResult.value,
  };
  if (richUi) {
    value.rich_ui = richUi;
  } else {
    delete value.rich_ui;
  }
  return { value, diagnostics };
}

export function resolveSessionListActionPresentation(
  element: SessionListActionElement,
  supportedRichKinds: ReadonlySet<string> | readonly string[],
): SessionListActionPresentation {
  const richUi = element.rich_ui;
  const supportedSet = supportedRichKinds as ReadonlySet<string>;
  const supports =
    typeof supportedSet.has === 'function'
      ? supportedSet.has(richUi?.kind ?? '')
      : (supportedRichKinds as readonly string[]).includes(richUi?.kind ?? '');
  if (richUi && supports) {
    return { mode: 'rich', richUi };
  }
  return { mode: 'dialog', dialog: element.dialog };
}

function stringifyDialogInitialValue(value: unknown): string {
  if (value === undefined || value === null) return '';
  return String(value);
}

export function resolveActionDialogInitialValue(
  field: ActionDialogInput,
  context: ActionDialogPrefillContext | undefined,
): string {
  if (field.type === 'secret' || field.type === 'password') {
    return '';
  }
  const source = field.prefill_from;
  if (typeof source === 'string' && source) {
    let root: unknown;
    let path: string | null = null;
    if (source.startsWith('$session.')) {
      root = context?.session;
      path = source.slice('$session.'.length);
    } else if (source.startsWith('$message.')) {
      root = context?.message;
      path = source.slice('$message.'.length);
    }
    if (path) {
      const resolved = resolveSessionListPath(root, path);
      if (
        resolved.found &&
        resolved.value !== undefined &&
        resolved.value !== null &&
        resolved.value !== ''
      ) {
        return stringifyDialogInitialValue(resolved.value);
      }
    }
  }
  return stringifyDialogInitialValue(field.default);
}

export function buildActionDialogInitialValues(
  inputs: readonly ActionDialogInput[],
  context?: ActionDialogPrefillContext,
): Record<string, string> {
  const values: Record<string, string> = {};
  for (const field of inputs) {
    if (!field || typeof field.name !== 'string' || !field.name) continue;
    values[field.name] = resolveActionDialogInitialValue(field, context);
  }
  return values;
}