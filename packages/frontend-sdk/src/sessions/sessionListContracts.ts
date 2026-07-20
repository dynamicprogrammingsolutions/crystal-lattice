import type { ActionUiElement, SessionListFieldElement } from '../types/plugins';

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

export interface SessionListRichUi {
  kind: string;
  [key: string]: unknown;
}

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
    if (!isRecord(raw.rich_ui) || typeof raw.rich_ui.kind !== 'string' || !raw.rich_ui.kind) {
      diagnostics.push({
        code: 'invalid_session_list_rich_ui',
        message: 'Ignoring malformed rich_ui while preserving the ordinary action.',
        elementId: raw.id,
      });
    } else {
      richUi = raw.rich_ui as SessionListRichUi;
    }
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