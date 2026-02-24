import type { UiSchemaElement } from '../types/uiSchema';

/**
 * Evaluate a UI element condition against a message/context object.
 * Matches the Python spec in agent_core.ui_condition: leaf operators
 * eq, exists, empty; composition all, any, not.
 */
export function evaluateCondition(
  condition: unknown,
  context: Record<string, unknown>,
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
