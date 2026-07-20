import type { SessionListFieldElement } from '../types/plugins';
import type { SessionSummary } from '../types/sessions';
import { renderTemplate } from '../utils/uiSchema';
import {
  formatSessionListFieldValue,
  resolveSessionListPath,
} from './sessionListContracts';

export interface SessionListFieldGroups {
  titleFields: SessionListFieldElement[];
  subtitleFields: SessionListFieldElement[];
  metaFields: SessionListFieldElement[];
}

export interface SessionListPresentation {
  title: string;
  subtitle: string | null;
  meta: string | null;
}

function sortFields(fields: SessionListFieldElement[]): SessionListFieldElement[] {
  return [...fields].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
}

export function groupSessionListFields(fields: SessionListFieldElement[]): SessionListFieldGroups {
  const all = Array.isArray(fields) ? fields : [];
  return {
    titleFields: sortFields(all.filter((el) => (el as any)?.role === 'title')),
    subtitleFields: sortFields(all.filter((el) => (el as any)?.role === 'subtitle')),
    metaFields: sortFields(all.filter((el) => (el as any)?.role === 'meta')),
  };
}

export function deriveSessionListPresentationFromGroups(
  session: SessionSummary,
  groups: SessionListFieldGroups,
): SessionListPresentation {
  const supplied = session.presentation;
  if (
    supplied &&
    typeof supplied.title === 'string' &&
    supplied.title.length > 0 &&
    (supplied.subtitle === null || typeof supplied.subtitle === 'string') &&
    (supplied.meta === null || typeof supplied.meta === 'string')
  ) {
    return supplied;
  }

  const sessionIdPrefix = session.session_id?.slice(0, 8) ?? '';

  const title = (() => {
    for (const field of groups.titleFields) {
      const path = field.data;
      if (typeof path !== 'string' || !path) continue;
      const resolved = resolveSessionListPath(session, path);
      const value = resolved.found ? resolved.value : undefined;
      if (value === null || value === undefined || value === '') continue;
      const text = renderTemplate(
        field.template ?? '{{data}}',
        formatSessionListFieldValue(field, value),
      );
      if (text) return text;
    }

    if (session.preview && session.preview.trim()) {
      return session.preview;
    }

    return `Session ${sessionIdPrefix}`;
  })();

  const subtitle = (() => {
    for (const field of groups.subtitleFields) {
      const path = field.data;
      if (typeof path !== 'string' || !path) continue;
      const resolved = resolveSessionListPath(session, path);
      const value = resolved.found ? resolved.value : undefined;
      if (value === null || value === undefined || value === '') continue;
      const text = renderTemplate(
        field.template ?? '{{data}}',
        formatSessionListFieldValue(field, value),
      );
      if (text) return text;
    }
    return null;
  })();

  const meta = (() => {
    const parts: string[] = [];
    for (const field of groups.metaFields) {
      const path = field.data;
      if (typeof path !== 'string' || !path) continue;
      const resolved = resolveSessionListPath(session, path);
      const rawValue = resolved.found ? resolved.value : undefined;
      const valueForTemplate = formatSessionListFieldValue(field, rawValue);
      if (valueForTemplate === null || valueForTemplate === undefined || valueForTemplate === '') {
        continue;
      }
      const text = renderTemplate(field.template ?? '{{data}}', valueForTemplate);
      if (!text) continue;
      parts.push(text);
    }
    if (parts.length === 0) return null;
    return parts.join(' · ');
  })();

  return { title, subtitle, meta };
}

export function deriveSessionListPresentation(
  session: SessionSummary,
  fields: SessionListFieldElement[],
): SessionListPresentation {
  return deriveSessionListPresentationFromGroups(session, groupSessionListFields(fields));
}
