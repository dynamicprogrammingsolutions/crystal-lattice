import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

import type { SessionSummary } from '../types/sessions';
import {
  FRONTEND_FALLBACK_SESSION_SEARCH_ID,
  countActiveSessionListFilters,
  createSessionListFilterValues,
  evaluateSessionListFilters,
  normalizeSessionListFilterSchema,
  withFrontendFallbackSessionSearch,
} from './sessionListFilters';

const FIXTURES = JSON.parse(
  readFileSync(
    new URL(
      '../../../../test/fixture/session-list/v1/filter-cases.json',
      import.meta.url,
    ),
    'utf8',
  ),
) as any;

describe('session-list filter shared contract cases', () => {
  it.each(FIXTURES.normalization_cases)(
    'normalizes declaration: $name',
    (fixture: any) => {
      const schema = normalizeSessionListFilterSchema([fixture.raw]);
      expect(schema.filters.length === 1).toBe(fixture.expected.valid);
      if (fixture.expected.valid) {
        expect(schema.filters[0].type).toBe(fixture.expected.type);
        expect(schema.filters[0].main_search).toBe(
          fixture.expected.main_search,
        );
      } else {
        expect(schema.diagnostics.map((item) => item.code)).toContain(
          fixture.expected.diagnostic_code,
        );
      }
    },
  );

  it.each(FIXTURES.schema_cases)('composes schema: $name', (fixture: any) => {
    const schema = normalizeSessionListFilterSchema(fixture.elements);
    expect(schema.filters.map((filter) => filter.id)).toEqual(
      fixture.expected.filter_ids,
    );
    expect(schema.mainSearch?.id ?? null).toBe(
      fixture.expected.main_search_id,
    );
    expect(schema.mainSearchConflict).toBe(
      fixture.expected.main_search_conflict,
    );
    if (fixture.expected.diagnostic_code) {
      expect(schema.diagnostics.map((item) => item.code)).toContain(
        fixture.expected.diagnostic_code,
      );
    }
  });

  it.each(FIXTURES.evaluation_cases)(
    'evaluates summaries: $name',
    (fixture: any) => {
      const schema = normalizeSessionListFilterSchema(fixture.elements);
      const base = createSessionListFilterValues(
        schema,
        fixture.apply_defaults ? 'defaults' : 'show_all',
      );
      const values = { ...base, ...fixture.values };
      const result = evaluateSessionListFilters(
        fixture.sessions as SessionSummary[],
        schema,
        values,
      );
      expect(result.sessions.map((session) => session.session_id)).toEqual(
        fixture.expected_ids,
      );
    },
  );

  it('supplies a frontend fallback search without hiding schema diagnostics', () => {
    const conflicted = normalizeSessionListFilterSchema(
      FIXTURES.schema_cases.find(
        (fixture: any) =>
          fixture.name === 'competing main searches are both excluded',
      ).elements,
    );
    const frontend = withFrontendFallbackSessionSearch(conflicted);

    expect(frontend.mainSearch?.id).toBe(
      FRONTEND_FALLBACK_SESSION_SEARCH_ID,
    );
    expect(frontend.usesFrontendFallbackSearch).toBe(true);
    expect(frontend.mainSearchConflict).toBe(true);
    expect(frontend.diagnostics.map((item) => item.code)).toContain(
      'ambiguous_session_list_main_search',
    );
  });

  it('creates default and Show-all values and counts only active non-main filters', () => {
    const schema = withFrontendFallbackSessionSearch(
      normalizeSessionListFilterSchema([
        {
          ui_type: 'session_list_filter',
          id: 'archived',
          label: 'Archived',
          data: 'metadata.archived',
          type: 'boolean',
          match: 'equals',
          default: false,
        },
      ]),
    );

    const defaults = createSessionListFilterValues(schema);
    const showAll = createSessionListFilterValues(schema, 'show_all');
    expect(defaults).toEqual({
      [FRONTEND_FALLBACK_SESSION_SEARCH_ID]: '',
      archived: false,
    });
    expect(showAll).toEqual({
      [FRONTEND_FALLBACK_SESSION_SEARCH_ID]: '',
      archived: null,
    });
    expect(
      countActiveSessionListFilters(schema, defaults, {
        excludeMainSearch: true,
      }),
    ).toBe(1);
    expect(
      countActiveSessionListFilters(schema, showAll, {
        excludeMainSearch: true,
      }),
    ).toBe(0);
  });
});