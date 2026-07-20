import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

import {
  buildActionDialogInitialValues,
  normalizeSessionListActionElement,
  normalizeSessionListFieldElement,
  normalizeSessionListOrderSpec,
  resolveSessionListActionPresentation,
  resolveSessionListPath,
  type ActionDialogInput,
} from './sessionListContracts';
import {
  deriveSessionListPresentation,
} from './sessionListPresentation';
import type { SessionListFieldElement } from '../types/plugins';
import type { SessionSummary } from '../types/sessions';

const FIXTURES = JSON.parse(
  readFileSync(
    new URL(
      '../../../../test/fixture/session-list/v1/contract-cases.json',
      import.meta.url,
    ),
    'utf8',
  ),
) as any;

describe('session-list shared contract cases', () => {
  it.each(FIXTURES.path_cases)('resolves path case: $name', (fixture: any) => {
    const result = resolveSessionListPath(fixture.root, fixture.path);
    expect(result.found).toBe(fixture.expected.found);
    if (fixture.expected.found) {
      expect(result.value).toEqual(fixture.expected.value);
    } else {
      expect(Object.prototype.hasOwnProperty.call(result, 'value')).toBe(false);
    }
  });

  it.each(FIXTURES.presentation_cases)(
    'derives presentation case: $name',
    (fixture: any) => {
      const fields = fixture.fields
        .map((raw: unknown) => normalizeSessionListFieldElement(raw).value)
        .filter((value: unknown): value is SessionListFieldElement => value !== null);
      expect(
        deriveSessionListPresentation(fixture.summary as SessionSummary, fields),
      ).toEqual(fixture.expected);
    },
  );

  it.each(FIXTURES.order_spec_cases)(
    'normalizes order case: $name',
    (fixture: any) => {
      const result = normalizeSessionListOrderSpec(fixture.raw);
      expect(result.value !== null).toBe(fixture.expected.valid);
      if (fixture.expected.valid) {
        expect(result.value).toEqual(fixture.expected.value);
      } else {
        expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toContain(
          fixture.expected.diagnostic_code,
        );
      }
    },
  );

  it.each(FIXTURES.action_cases)(
    'normalizes ordinary action case: $name',
    (fixture: any) => {
      const result = normalizeSessionListActionElement(fixture.raw);
      expect(result.value !== null).toBe(fixture.expected.valid);
      if (!result.value) {
        expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toContain(
          fixture.expected.diagnostic_code,
        );
        return;
      }

      expect(result.value.dialog.kind).toBe(fixture.expected.dialog_kind);
      if (fixture.expected.rich_state === 'preserved') {
        expect(result.value.rich_ui).toEqual(fixture.raw.rich_ui);
      } else {
        expect(result.value.rich_ui).toBeUndefined();
      }
      expect(
        resolveSessionListActionPresentation(result.value, []).mode,
      ).toBe(fixture.expected.fallback_mode);
      if (fixture.expected.diagnostic_code) {
        expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toContain(
          fixture.expected.diagnostic_code,
        );
      }
    },
  );

  it.each(FIXTURES.prefill_cases)(
    'initializes dialog case: $name',
    (fixture: any) => {
      const values = buildActionDialogInitialValues(
        [fixture.field as ActionDialogInput],
        fixture.context,
      );
      expect(values[fixture.field.name]).toBe(fixture.expected);
    },
  );

  it('selects rich presentation only for a supported kind', () => {
    const normalized = normalizeSessionListActionElement(
      FIXTURES.action_cases.find(
        (fixture: any) => fixture.name === 'unknown rich kind is preserved but unsupported',
      ).raw,
    );
    expect(normalized.value).not.toBeNull();
    expect(
      resolveSessionListActionPresentation(normalized.value!, ['future_kind']),
    ).toEqual({
      mode: 'rich',
      richUi: {
        kind: 'future_kind',
        value_path: 'metadata.value',
      },
    });
  });

  it('prefers application-derived presentation over local field evaluation', () => {
    const session: SessionSummary = {
      session_id: 'session',
      modified: 1,
      preview: 'preview',
      metadata: { title: 'local title' },
      presentation: {
        title: 'application title',
        subtitle: 'application subtitle',
        meta: null,
      },
    };
    const fields: SessionListFieldElement[] = [
      {
        ui_type: 'session_list_field',
        plugin: 'fixture',
        id: 'title',
        role: 'title',
        data: 'metadata.title',
      },
    ];

    expect(deriveSessionListPresentation(session, fields)).toEqual(
      session.presentation,
    );
  });
});