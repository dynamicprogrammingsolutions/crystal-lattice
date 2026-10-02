import type { ApplicationUiElement } from '../types/plugins';
import type { SessionSummary } from '../types/sessions';
import {
  resolveSessionListPath,
  type SessionListContractDiagnostic,
} from './sessionListContracts';

export type SessionListFilterType = 'text' | 'boolean' | 'select' | 'datetime';
export type SessionListFilterMatch =
  | 'contains'
  | 'equals'
  | 'one_of'
  | 'before'
  | 'on_or_before'
  | 'after'
  | 'on_or_after';
export type SessionListOptionTone =
  | 'primary'
  | 'highlight'
  | 'warning'
  | 'success'
  | 'danger'
  | 'muted';
export type SessionListOptionValue = string | boolean;

export interface SessionListOption {
  value: SessionListOptionValue;
  label: string;
  icon?: string;
  tone?: SessionListOptionTone;
}

export interface SessionListFilterElement {
  ui_type: 'session_list_filter';
  id: string;
  plugin?: string;
  label: string;
  icon?: string;
  order: number;
  data: readonly string[];
  type: SessionListFilterType;
  match: SessionListFilterMatch;
  multiple: boolean;
  case_sensitive: boolean;
  has_missing_value: boolean;
  missing_value?: unknown;
  default: unknown;
  options: readonly SessionListOption[];
  main_search: boolean;
  declaration_index: number;
}

export interface SessionListFilterSchema {
  filters: readonly SessionListFilterElement[];
  mainSearch: SessionListFilterElement | null;
  identity: string;
  diagnostics: readonly SessionListContractDiagnostic[];
  mainSearchConflict: boolean;
  usesFrontendFallbackSearch?: boolean;
}

export type SessionListFilterValues = Readonly<Record<string, unknown>>;

export interface SessionListFilterEvaluation {
  sessions: SessionSummary[];
  diagnostics: SessionListContractDiagnostic[];
}

export const FRONTEND_FALLBACK_SESSION_SEARCH_ID =
  '__frontend_fallback_session_search__';

const OPTION_TONES = new Set<SessionListOptionTone>([
  'primary',
  'highlight',
  'warning',
  'success',
  'danger',
  'muted',
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isOptionValue(value: unknown): value is SessionListOptionValue {
  return typeof value === 'string' || typeof value === 'boolean';
}

function typedValueKey(value: unknown): string {
  return `${typeof value}:${String(value)}`;
}

function typedEqual(left: unknown, right: unknown): boolean {
  return typeof left === typeof right && left === right;
}

function datetimeTimestamp(
  value: unknown,
  options: { runtimeValue: boolean },
): number | null {
  if (
    !options.runtimeValue &&
    typeof value === 'number' &&
    Number.isFinite(value)
  ) {
    return value * 1000;
  }
  if (
    typeof value !== 'string' ||
    !value ||
    !/(?:Z|[+-]\d{2}:\d{2})$/i.test(value)
  ) {
    return null;
  }
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function diagnostic(
  code: string,
  message: string,
  raw?: Record<string, unknown>,
  details?: Record<string, unknown>,
): SessionListContractDiagnostic {
  const result: SessionListContractDiagnostic = { code, message };
  if (typeof raw?.id === 'string' && raw.id) {
    result.elementId = raw.id;
  }
  if (typeof raw?.plugin === 'string' && raw.plugin) {
    result.details = {
      ...(details ?? {}),
      plugin: raw.plugin,
    };
  } else if (details) {
    result.details = details;
  }
  return result;
}

function normalizeOptions(
  raw: unknown,
  element: Record<string, unknown>,
  booleanFilter: boolean,
): {
  options: SessionListOption[] | null;
  diagnostic?: SessionListContractDiagnostic;
} {
  if (raw === undefined && booleanFilter) {
    return { options: [] };
  }
  if (!Array.isArray(raw) || (!booleanFilter && raw.length === 0)) {
    return {
      options: null,
      diagnostic: diagnostic(
        'invalid_session_list_filter',
        booleanFilter
          ? 'session_list_filter.options must be a list when provided.'
          : 'session_list_filter.options must be a non-empty list.',
        element,
      ),
    };
  }

  const options: SessionListOption[] = [];
  const seen = new Set<string>();
  for (const rawOption of raw) {
    if (!isRecord(rawOption)) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          'Every session_list_filter option must be an object.',
          element,
        ),
      };
    }
    const value = rawOption.value;
    if (
      !isOptionValue(value) ||
      (booleanFilter && typeof value !== 'boolean')
    ) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          booleanFilter
            ? 'Boolean filter option values must be booleans.'
            : 'Select option values must be strings or booleans.',
          element,
        ),
      };
    }
    if (
      !booleanFilter &&
      typeof value === 'string' &&
      value.toLowerCase() === 'any'
    ) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          "Select option value 'any' is reserved for the inactive value.",
          element,
        ),
      };
    }
    if (typeof rawOption.label !== 'string' || !rawOption.label) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          'Every session_list_filter option requires a non-empty label.',
          element,
        ),
      };
    }
    if (rawOption.icon !== undefined && typeof rawOption.icon !== 'string') {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          'session_list_filter option icons must be strings.',
          element,
        ),
      };
    }
    if (
      rawOption.tone !== undefined &&
      !OPTION_TONES.has(rawOption.tone as SessionListOptionTone)
    ) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          'session_list_filter option tone is not supported.',
          element,
        ),
      };
    }
    const key = typedValueKey(value);
    if (seen.has(key)) {
      return {
        options: null,
        diagnostic: diagnostic(
          'invalid_session_list_filter',
          'session_list_filter option values must be unique by type and value.',
          element,
        ),
      };
    }
    seen.add(key);
    options.push({
      value,
      label: rawOption.label,
      ...(typeof rawOption.icon === 'string' ? { icon: rawOption.icon } : {}),
      ...(typeof rawOption.tone === 'string'
        ? { tone: rawOption.tone as SessionListOptionTone }
        : {}),
    });
  }
  return { options };
}

function isDeclaredOption(
  value: unknown,
  options: readonly SessionListOption[],
): boolean {
  return options.some((option) => typedEqual(value, option.value));
}

function normalizeFilter(
  raw: Record<string, unknown>,
  declarationIndex: number,
): {
  value: SessionListFilterElement | null;
  diagnostics: SessionListContractDiagnostic[];
} {
  const fail = (message: string) => ({
    value: null,
    diagnostics: [diagnostic('invalid_session_list_filter', message, raw)],
  });

  if (typeof raw.id !== 'string' || !raw.id) {
    return fail('session_list_filter.id must be a non-empty string.');
  }
  if (typeof raw.label !== 'string' || !raw.label) {
    return fail('session_list_filter.label must be a non-empty string.');
  }
  if (raw.icon !== undefined && typeof raw.icon !== 'string') {
    return fail('session_list_filter.icon must be a string.');
  }
  const order = raw.order ?? 0;
  if (
    typeof order !== 'number' ||
    !Number.isFinite(order)
  ) {
    return fail('session_list_filter.order must be a finite number.');
  }

  let data: string[];
  if (typeof raw.data === 'string' && raw.data) {
    data = [raw.data];
  } else if (
    Array.isArray(raw.data) &&
    raw.data.length > 0 &&
    raw.data.every((path) => typeof path === 'string' && path.length > 0)
  ) {
    data = [...raw.data];
  } else {
    return fail(
      'session_list_filter.data must be a non-empty path or path list.',
    );
  }

  let type: SessionListFilterType;
  let match: SessionListFilterMatch;
  let multiple = false;
  let caseSensitive = false;
  let options: SessionListOption[] = [];
  let defaultValue: unknown;

  if (raw.type === 'text') {
    type = 'text';
    if (raw.match !== 'contains' && raw.match !== 'equals') {
      return fail('Text filters support contains or equals.');
    }
    match = raw.match;
    if (Object.prototype.hasOwnProperty.call(raw, 'multiple')) {
      return fail(
        'session_list_filter.multiple is valid only for select filters.',
      );
    }
    if (Object.prototype.hasOwnProperty.call(raw, 'options')) {
      return fail('Text filters do not support options.');
    }
    const rawCaseSensitive = raw.case_sensitive ?? false;
    if (typeof rawCaseSensitive !== 'boolean') {
      return fail('Text filter case_sensitive must be a boolean.');
    }
    caseSensitive = rawCaseSensitive;
    defaultValue = raw.default ?? '';
    if (typeof defaultValue !== 'string') {
      return fail('Text filter default must be a string.');
    }
  } else if (raw.type === 'boolean') {
    type = 'boolean';
    if (raw.match !== 'equals') {
      return fail('Boolean filters support equals only.');
    }
    match = 'equals';
    if (Object.prototype.hasOwnProperty.call(raw, 'multiple')) {
      return fail(
        'session_list_filter.multiple is valid only for select filters.',
      );
    }
    if (Object.prototype.hasOwnProperty.call(raw, 'case_sensitive')) {
      return fail('case_sensitive is valid only for text filters.');
    }
    const normalizedOptions = normalizeOptions(raw.options, raw, true);
    if (!normalizedOptions.options) {
      return {
        value: null,
        diagnostics: [normalizedOptions.diagnostic!],
      };
    }
    options = normalizedOptions.options;
    defaultValue = raw.default ?? null;
    if (defaultValue !== null && typeof defaultValue !== 'boolean') {
      return fail('Boolean filter default must be null, true, or false.');
    }
  } else if (raw.type === 'select') {
    type = 'select';
    if (Object.prototype.hasOwnProperty.call(raw, 'case_sensitive')) {
      return fail('case_sensitive is valid only for text filters.');
    }
    const rawMultiple = raw.multiple ?? false;
    if (typeof rawMultiple !== 'boolean') {
      return fail('Select filter multiple must be a boolean.');
    }
    multiple = rawMultiple;
    const expectedMatch: SessionListFilterMatch = multiple ? 'one_of' : 'equals';
    if (raw.match !== expectedMatch) {
      return fail(
        `${multiple ? 'Multiple' : 'Single'} select filters require ${expectedMatch}.`,
      );
    }
    match = expectedMatch;
    const normalizedOptions = normalizeOptions(raw.options, raw, false);
    if (!normalizedOptions.options) {
      return {
        value: null,
        diagnostics: [normalizedOptions.diagnostic!],
      };
    }
    options = normalizedOptions.options;
    defaultValue =
      raw.default !== undefined ? raw.default : multiple ? [] : null;
    if (multiple) {
      if (!Array.isArray(defaultValue)) {
        return fail('Multiple-select filter default must be a list.');
      }
      const seen = new Set<string>();
      for (const value of defaultValue) {
        const key = typedValueKey(value);
        if (!isDeclaredOption(value, options) || seen.has(key)) {
          return fail(
            'Multiple-select defaults must be unique declared option values.',
          );
        }
        seen.add(key);
      }
    } else if (
      defaultValue !== null &&
      !isDeclaredOption(defaultValue, options)
    ) {
      return fail(
        'Single-select default must be null or a declared option value.',
      );
    }
  } else if (raw.type === 'datetime') {
    type = 'datetime';
    if (
      raw.match !== 'before' &&
      raw.match !== 'on_or_before' &&
      raw.match !== 'after' &&
      raw.match !== 'on_or_after'
    ) {
      return fail(
        'Datetime filters support before, on_or_before, after, or on_or_after.',
      );
    }
    match = raw.match;
    if (Object.prototype.hasOwnProperty.call(raw, 'multiple')) {
      return fail(
        'session_list_filter.multiple is valid only for select filters.',
      );
    }
    if (Object.prototype.hasOwnProperty.call(raw, 'case_sensitive')) {
      return fail('case_sensitive is valid only for text filters.');
    }
    if (Object.prototype.hasOwnProperty.call(raw, 'options')) {
      return fail('Datetime filters do not support options.');
    }
    defaultValue = raw.default ?? null;
    if (
      defaultValue !== null &&
      datetimeTimestamp(defaultValue, { runtimeValue: true }) === null
    ) {
      return fail(
        'Datetime filter default must be null or a timezone-aware ISO-8601 string.',
      );
    }
  } else {
    return fail(
      'session_list_filter.type must be text, boolean, select, or datetime.',
    );
  }

  const mainSearch = raw.main_search ?? false;
  if (typeof mainSearch !== 'boolean') {
    return fail('session_list_filter.main_search must be a boolean.');
  }
  if (mainSearch && type !== 'text') {
    return fail('main_search is valid only for text filters.');
  }

  return {
    value: {
      ui_type: 'session_list_filter',
      id: raw.id,
      ...(typeof raw.plugin === 'string' && raw.plugin
        ? { plugin: raw.plugin }
        : {}),
      label: raw.label,
      ...(typeof raw.icon === 'string' ? { icon: raw.icon } : {}),
      order,
      data,
      type,
      match,
      multiple,
      case_sensitive: caseSensitive,
      has_missing_value: Object.prototype.hasOwnProperty.call(
        raw,
        'missing_value',
      ),
      ...(Object.prototype.hasOwnProperty.call(raw, 'missing_value')
        ? { missing_value: raw.missing_value }
        : {}),
      default: defaultValue,
      options,
      main_search: mainSearch,
      declaration_index: declarationIndex,
    },
    diagnostics: [],
  };
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(stableValue);
  }
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, stableValue(value[key])]),
    );
  }
  return value;
}

function filterIdentityValue(filter: SessionListFilterElement): unknown {
  return {
    ui_type: filter.ui_type,
    id: filter.id,
    plugin: filter.plugin,
    label: filter.label,
    icon: filter.icon,
    order: filter.order,
    data: filter.data,
    type: filter.type,
    match: filter.match,
    multiple: filter.multiple,
    case_sensitive: filter.case_sensitive,
    has_missing_value: filter.has_missing_value,
    missing_value: filter.missing_value,
    default: filter.default,
    options: filter.options,
    main_search: filter.main_search,
  };
}

export function normalizeSessionListFilterSchema(
  elements: readonly ApplicationUiElement[] | readonly unknown[],
): SessionListFilterSchema {
  const diagnostics: SessionListContractDiagnostic[] = [];
  let filters: SessionListFilterElement[] = [];
  elements.forEach((raw, declarationIndex) => {
    if (!isRecord(raw) || raw.ui_type !== 'session_list_filter') {
      return;
    }
    const normalized = normalizeFilter(raw, declarationIndex);
    diagnostics.push(...normalized.diagnostics);
    if (normalized.value) {
      filters.push(normalized.value);
    }
  });

  const declaredMainSearches = filters.filter((filter) => filter.main_search);
  const byId = new Map<string, SessionListFilterElement[]>();
  filters.forEach((filter) => {
    byId.set(filter.id, [...(byId.get(filter.id) ?? []), filter]);
  });
  const duplicateIds = new Set(
    [...byId.entries()]
      .filter(([, declarations]) => declarations.length > 1)
      .map(([id]) => id),
  );
  [...duplicateIds].sort().forEach((id) => {
    diagnostics.push({
      code: 'duplicate_session_list_filter_id',
      message:
        `Multiple session-list filters declare id ${JSON.stringify(id)}; ` +
        'all declarations with that id were ignored.',
      elementId: id,
      details: {
        plugins: (byId.get(id) ?? []).map((filter) => filter.plugin ?? null),
      },
    });
  });
  filters = filters.filter((filter) => !duplicateIds.has(filter.id));

  const mainSearches = filters.filter((filter) => filter.main_search);
  const mainSearchConflict = declaredMainSearches.length > 1;
  let mainSearch: SessionListFilterElement | null = null;
  if (mainSearchConflict) {
    const conflictingIds = declaredMainSearches.map((filter) => filter.id);
    diagnostics.push({
      code: 'ambiguous_session_list_main_search',
      message:
        'Multiple valid session-list filters declare main_search; none was selected.',
      details: { filter_ids: conflictingIds },
    });
    filters = filters.filter((filter) => !filter.main_search);
  } else {
    mainSearch = mainSearches[0] ?? null;
  }

  filters.sort(
    (left, right) =>
      left.order - right.order ||
      left.declaration_index - right.declaration_index,
  );
  const identity = JSON.stringify(
    stableValue({
      filters: filters.map(filterIdentityValue),
      main_search_id: mainSearch?.id ?? null,
      main_search_conflict: mainSearchConflict,
    }),
  );
  return {
    filters,
    mainSearch,
    identity,
    diagnostics,
    mainSearchConflict,
  };
}

const FRONTEND_FALLBACK_MAIN_SEARCH: SessionListFilterElement = {
  ui_type: 'session_list_filter',
  id: FRONTEND_FALLBACK_SESSION_SEARCH_ID,
  label: 'Search',
  icon: 'search',
  order: 0,
  data: [
    'session_id',
    'preview',
    'presentation.title',
    'presentation.subtitle',
    'presentation.meta',
  ],
  type: 'text',
  match: 'contains',
  multiple: false,
  case_sensitive: false,
  has_missing_value: false,
  default: '',
  options: [],
  main_search: true,
  declaration_index: -1,
};

export function withFrontendFallbackSessionSearch(
  schema: SessionListFilterSchema,
): SessionListFilterSchema {
  if (schema.mainSearch) {
    return schema;
  }
  const filters = [FRONTEND_FALLBACK_MAIN_SEARCH, ...schema.filters];
  return {
    ...schema,
    filters,
    mainSearch: FRONTEND_FALLBACK_MAIN_SEARCH,
    identity: `${schema.identity}:frontend-fallback-search`,
    usesFrontendFallbackSearch: true,
  };
}

export function inactiveSessionListFilterValue(
  filter: SessionListFilterElement,
): unknown {
  if (filter.type === 'text') {
    return '';
  }
  if (filter.type === 'select' && filter.multiple) {
    return [];
  }
  return null;
}

export function createSessionListFilterValues(
  schema: SessionListFilterSchema,
  mode: 'defaults' | 'show_all' = 'defaults',
): SessionListFilterValues {
  return Object.fromEntries(
    schema.filters.map((filter) => [
      filter.id,
      mode === 'defaults'
        ? filter.default
        : inactiveSessionListFilterValue(filter),
    ]),
  );
}

export function validateSessionListFilterValue(
  filter: SessionListFilterElement,
  value: unknown,
): string | null {
  if (filter.type === 'text') {
    return typeof value === 'string' ? null : 'must be a string';
  }
  if (filter.type === 'boolean') {
    return value === null || typeof value === 'boolean'
      ? null
      : 'must be null, true, or false';
  }
  if (filter.type === 'datetime') {
    return value === null ||
      datetimeTimestamp(value, { runtimeValue: true }) !== null
      ? null
      : 'must be null or a timezone-aware ISO-8601 string';
  }
  if (filter.multiple) {
    if (!Array.isArray(value)) {
      return 'must be a list of declared option values';
    }
    const seen = new Set<string>();
    for (const selected of value) {
      const key = typedValueKey(selected);
      if (!isDeclaredOption(selected, filter.options) || seen.has(key)) {
        return 'must contain unique declared option values';
      }
      seen.add(key);
    }
    return null;
  }
  return value === null || isDeclaredOption(value, filter.options)
    ? null
    : 'must be null or a declared option value';
}

export function reconcileSessionListFilterValues(
  schema: SessionListFilterSchema,
  values: SessionListFilterValues,
): SessionListFilterValues {
  const next: Record<string, unknown> = {};
  for (const filter of schema.filters) {
    const value = values[filter.id];
    next[filter.id] =
      validateSessionListFilterValue(filter, value) === null
        ? value
        : filter.default;
  }
  return next;
}

export function isSessionListFilterActive(
  filter: SessionListFilterElement,
  value: unknown,
): boolean {
  if (filter.type === 'text') {
    return typeof value === 'string' && value !== '';
  }
  if (filter.type === 'select' && filter.multiple) {
    return Array.isArray(value) && value.length > 0;
  }
  return value !== null && value !== undefined;
}

export function countActiveSessionListFilters(
  schema: SessionListFilterSchema,
  values: SessionListFilterValues,
  options: { excludeMainSearch?: boolean } = {},
): number {
  return schema.filters.filter((filter) => {
    if (options.excludeMainSearch && filter.id === schema.mainSearch?.id) {
      return false;
    }
    return isSessionListFilterActive(filter, values[filter.id]);
  }).length;
}

function resolvedValueMatches(
  filter: SessionListFilterElement,
  resolvedValue: unknown,
  runtimeValue: unknown,
): boolean {
  if (filter.type === 'text') {
    if (typeof resolvedValue !== 'string' || typeof runtimeValue !== 'string') {
      return false;
    }
    const candidate = filter.case_sensitive
      ? resolvedValue
      : resolvedValue.toLowerCase();
    const query = filter.case_sensitive
      ? runtimeValue
      : runtimeValue.toLowerCase();
    return filter.match === 'equals'
      ? candidate === query
      : candidate.includes(query);
  }
  if (filter.type === 'boolean') {
    return typeof resolvedValue === 'boolean' && typedEqual(resolvedValue, runtimeValue);
  }
  if (filter.type === 'datetime') {
    const candidate = datetimeTimestamp(resolvedValue, { runtimeValue: false });
    const query = datetimeTimestamp(runtimeValue, { runtimeValue: true });
    if (candidate === null || query === null) {
      return false;
    }
    if (filter.match === 'before') {
      return candidate < query;
    }
    if (filter.match === 'on_or_before') {
      return candidate <= query;
    }
    if (filter.match === 'after') {
      return candidate > query;
    }
    return candidate >= query;
  }
  if (filter.multiple) {
    return (
      Array.isArray(runtimeValue) &&
      runtimeValue.some((selected) => typedEqual(resolvedValue, selected))
    );
  }
  return typedEqual(resolvedValue, runtimeValue);
}

export function evaluateSessionListFilters(
  sessions: readonly SessionSummary[],
  schema: SessionListFilterSchema,
  values: SessionListFilterValues,
): SessionListFilterEvaluation {
  const diagnostics = [...schema.diagnostics];
  const active: Array<[SessionListFilterElement, unknown]> = [];
  for (const filter of schema.filters) {
    const value = values[filter.id];
    const valueError = validateSessionListFilterValue(filter, value);
    if (valueError) {
      diagnostics.push({
        code: 'invalid_session_list_filter_value',
        message: `Value for session-list filter ${JSON.stringify(filter.id)} ${valueError}.`,
        elementId: filter.id,
      });
      continue;
    }
    if (isSessionListFilterActive(filter, value)) {
      active.push([filter, value]);
    }
  }
  if (active.length === 0) {
    return { sessions: sessions as SessionSummary[], diagnostics };
  }

  return {
    sessions: sessions.filter((session) =>
      active.every(([filter, runtimeValue]) =>
        filter.data.some((path) => {
          const resolved = resolveSessionListPath(session, path);
          if (!resolved.found && !filter.has_missing_value) {
            return false;
          }
          const candidate = resolved.found
            ? resolved.value
            : filter.missing_value;
          return resolvedValueMatches(filter, candidate, runtimeValue);
        }),
      ),
    ),
    diagnostics,
  };
}
