import type { SessionListFieldElement } from '../types/plugins';
import type { SessionSummary } from '../types/sessions';
import { extractByPath, renderTemplate } from '../utils/uiSchema';

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
  const sessionIdPrefix = session.session_id?.slice(0, 8) ?? '';

  const title = (() => {
    for (const field of groups.titleFields) {
      const path = field.data;
      if (typeof path !== 'string' || !path) continue;
      const value = extractByPath(session as any, path);
      if (value === null || value === undefined || value === '') continue;
      const text = renderTemplate(field.template ?? '{{data}}', value);
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
      const value = extractByPath(session as any, path);
      if (value === null || value === undefined || value === '') continue;
      const text = renderTemplate(field.template ?? '{{data}}', value);
      if (text) return text;
    }
    return null;
  })();

  const meta = (() => {
    const parts: string[] = [];
    for (const field of groups.metaFields) {
      const path = field.data;
      if (typeof path !== 'string' || !path) continue;
      const rawValue = extractByPath(session as any, path);
      let valueForTemplate: any = rawValue;
      const metadata = (field as any).metadata || {};
      if (metadata.format === 'datetime' && typeof rawValue === 'number') {
        valueForTemplate = new Date(rawValue * 1000).toLocaleString();
      }
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
