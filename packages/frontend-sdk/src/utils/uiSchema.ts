import type { UiSchemaElement } from '../types/uiSchema';

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
