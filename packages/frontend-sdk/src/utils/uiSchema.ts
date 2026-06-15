import type { UiSchemaElement } from '../types/uiSchema';

export interface NormalizedSelectOption {
  value: string;
  label: string;
}

export function normalizeSelectOptions(raw: unknown): NormalizedSelectOption[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((option) => {
      if (typeof option === 'string') {
        return { value: option, label: option };
      }
      if (option && typeof option === 'object') {
        const record = option as Record<string, unknown>;
        const value =
          typeof record.value === 'string'
            ? record.value
            : record.value !== undefined && record.value !== null
              ? String(record.value)
              : '';
        if (!value) return null;
        const label = typeof record.label === 'string' ? record.label : value;
        return { value, label };
      }
      return null;
    })
    .filter((value): value is NormalizedSelectOption => value !== null);
}

/**
 * Evaluate a UI element condition against a message/context object.
 * Matches the Python spec in agent_core.ui_condition: leaf operators
 * eq, exists, empty; composition all, any, not.
 */
export function evaluateCondition(
  condition: unknown,
  context: object,
): boolean {
  if (condition == null || typeof condition !== 'object' || Array.isArray(condition)) {
    return true;
  }
  const c = condition as Record<string, unknown>;

  if ('all' in c) {
    const sub = c.all;
    if (!Array.isArray(sub)) return true;
    return sub.every((item) => evaluateCondition(item, context));
  }
  if ('any' in c) {
    const sub = c.any;
    if (!Array.isArray(sub)) return true;
    return sub.some((item) => evaluateCondition(item, context));
  }
  if ('not' in c) {
    return !evaluateCondition(c.not, context);
  }

  const path = c.path;
  if (typeof path !== 'string' || !path) return true;
  const value = extractByPath(context as any, path);

  if ('eq' in c) {
    return value === c.eq;
  }
  if ('exists' in c) {
    const want = c.exists;
    if (want === true) return value !== undefined && value !== null;
    if (want === false) return value === undefined || value === null;
    return true;
  }
  if ('empty' in c) {
    const want = c.empty;
    const isEmpty =
      value == null ||
      value === '' ||
      (Array.isArray(value) && value.length === 0) ||
      (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0);
    return isEmpty === want;
  }

  return true;
}

export function formatValueForElement(el: UiSchemaElement, rawValue: any): any {
  const metadata = (el as any)?.metadata || {};
  if (metadata.format === 'datetime') {
    if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
      return new Date(rawValue * 1000).toLocaleString();
    }
    if (typeof rawValue === 'string' && rawValue) {
      const dt = new Date(rawValue);
      if (Number.isFinite(dt.getTime())) {
        return dt.toLocaleString();
      }
    }
  }
  return rawValue;
}

/**
 * Coerce a value to the appropriate type based on UI element type.
 *
 * This is used when saving values from UI inputs (which typically produce strings)
 * to ensure the stored values have correct types for downstream processing.
 *
 * Type mappings:
 * - "number" -> int (if no decimal) or float
 * - "boolean" / "checkbox" -> bool
 * - "text" / "string" -> string (stringified)
 * - "select" / "dropdown" / others -> unchanged (select values stay as strings)
 *
 * @param element - The UI schema element (must have a `type` field)
 * @param value - The value to coerce (typically a string from UI input)
 * @returns The coerced value
 */
export function coerceValueForElement(element: UiSchemaElement, value: unknown): unknown {
  const type = element?.type;

  if (type === 'number') {
    // Already a number - return as-is
    if (typeof value === 'number') {
      return value;
    }
    // Boolean -> float
    if (typeof value === 'boolean') {
      return value ? 1.0 : 0.0;
    }
    // String -> int or float
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed === '') {
        return value; // Return empty string unchanged
      }
      // Try int first, then float
      if (/^-?\d+$/.test(trimmed)) {
        const intVal = parseInt(trimmed, 10);
        if (Number.isFinite(intVal)) {
          return intVal;
        }
      }
      const floatVal = parseFloat(trimmed);
      if (Number.isFinite(floatVal)) {
        return floatVal;
      }
      // Not a valid number - return unchanged
      return value;
    }
    return value;
  }

  if (type === 'boolean' || type === 'checkbox') {
    // Already a boolean - return as-is
    if (typeof value === 'boolean') {
      return value;
    }
    // String -> boolean
    if (typeof value === 'string') {
      const lower = value.toLowerCase().trim();
      if (lower === 'true' || lower === '1' || lower === 'yes' || lower === 'on') {
        return true;
      }
      if (lower === 'false' || lower === '0' || lower === 'no' || lower === 'off' || lower === '') {
        return false;
      }
      // Unknown string value - return unchanged
      return value;
    }
    // Number -> boolean
    if (typeof value === 'number') {
      return Boolean(value);
    }
    return value;
  }

  if (type === 'text' || type === 'string') {
    return value !== null && value !== undefined ? String(value) : value;
  }

  // "select", "dropdown", or unknown types - return unchanged
  // Select values should stay as strings since options are string values
  return value;
}

export function extractByPath(obj: any, path: string | undefined | null): any {
  if (!obj || typeof path !== 'string' || !path) return null;
  const parts = path.split('.');
  let current: any = obj;
  for (const part of parts) {
    if (current && typeof current === 'object' && !Array.isArray(current)) {
      if (!(part in current)) return null;
      current = current[part];
    } else if (Array.isArray(current)) {
      const idx = Number(part);
      if (!Number.isInteger(idx) || idx < 0 || idx >= current.length) {
        return null;
      }
      current = current[idx];
    } else {
      return null;
    }
  }
  return current;
}

export function renderTemplate(template: any, value: any): string {
  const text = value != null ? String(value) : '';
  if (typeof template !== 'string' || !template) return text;
  return template.replace('{{data}}', text).replace('{{ data }}', text);
}

export function filterFooterElements(all: UiSchemaElement[]): UiSchemaElement[] {
  return (all || []).filter(
    (el) => el && el.ui_type === 'message_footer' && typeof el.data === 'string' && !!el.data,
  );
}

export function filterStatusBarElements(all: UiSchemaElement[]): UiSchemaElement[] {
  return (all || []).filter(
    (el) => el && el.ui_type === 'status_bar' && typeof el.data === 'string' && !!el.data,
  );
}
