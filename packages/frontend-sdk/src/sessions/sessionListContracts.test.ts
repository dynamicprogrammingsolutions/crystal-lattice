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
  buildSessionListRichListDialogValues,
  getDefaultPinnedSessionListActionKeys,
  getSessionListRichActionPlacements,
  isSessionListRichActionPlacedAt,
  resolveSessionListRichActionState,
  selectSessionListRichActionForPlacement,
} from './sessionListRichActions';
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

  it('never prefills secret or password fields', () => {
    const values = buildActionDialogInitialValues(
      [
        { name: 'secret', type: 'secret', default: 'hidden' },
        { name: 'password', type: 'password', prefill_from: '$session.value' },
      ],
      { session: { value: 'hidden' } },
    );

    expect(values).toEqual({ secret: '', password: '' });
  });

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

  it('normalizes typed toggle and list presentations without changing fallback dialogs', () => {
    const toggle = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'toggle',
      label: 'Toggle',
      action_id: 'toggle',
      dialog: { kind: 'none' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.enabled',
        missing_value: false,
        active_value: true,
        default_pinned: true,
        appearance: {
          active: { tone: 'warning' },
          inactive: { tone: 'muted' },
        },
      },
    });
    const list = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'status',
      label: 'Status',
      action_id: 'status',
      dialog: { kind: 'form', inputs: [{ name: 'status', type: 'select' }] },
      rich_ui: {
        kind: 'list',
        value_path: 'metadata.status',
        missing_value: 'todo',
        input_name: 'status',
        options: [
          { value: 'todo', label: 'To do', tone: 'muted' },
          { value: 'done', label: 'Done', tone: 'success' },
        ],
      },
    });

    expect(toggle.value?.rich_ui).toMatchObject({ kind: 'toggle', default_pinned: true });
    expect(list.value?.rich_ui).toMatchObject({ kind: 'list', input_name: 'status' });
    expect(resolveSessionListActionPresentation(toggle.value!, []).mode).toBe('dialog');
    expect(resolveSessionListActionPresentation(list.value!, ['list']).mode).toBe('rich');
  });

  it('drops malformed known rich UI while preserving the ordinary action', () => {
    const result = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'invalid-toggle',
      label: 'Invalid toggle',
      action_id: 'invalid-toggle',
      dialog: { kind: 'confirm', message: 'Continue?' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.enabled',
        active_value: true,
        appearance: { active: { tone: 'warning' } },
      },
    });

    expect(result.value?.dialog.kind).toBe('confirm');
    expect(result.value?.rich_ui).toBeUndefined();
    expect(result.diagnostics.map((item) => item.code)).toContain(
      'invalid_session_list_rich_ui',
    );
  });

  it('normalizes a de-duplicated placement list while preserving future slots', () => {
    const result = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'placed-toggle',
      label: 'Placed toggle',
      action_id: 'placed-toggle',
      dialog: { kind: 'none' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.enabled',
        active_value: true,
        placements: [
          'header_trailing',
          'future_header_slot',
          'header_trailing',
          3,
          'actions_bar',
        ],
        appearance: {
          active: { tone: 'highlight' },
          inactive: { tone: 'muted' },
        },
      },
    });

    expect(result.value?.rich_ui).toMatchObject({
      kind: 'toggle',
      placements: ['header_trailing', 'future_header_slot', 'actions_bar'],
      appearance: { active: { tone: 'highlight' } },
    });
    expect(result.diagnostics.map((item) => item.code)).toContain(
      'invalid_session_list_rich_ui',
    );
    expect(getSessionListRichActionPlacements(result.value!)).toEqual([
      'header_trailing',
      'future_header_slot',
      'actions_bar',
    ]);
    expect(isSessionListRichActionPlacedAt(result.value!, 'actions_bar')).toBe(true);
  });

  it('uses declaration order to select one rich action for each header slot', () => {
    const first = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'first',
      label: 'First',
      action_id: 'first',
      dialog: { kind: 'none' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.first',
        active_value: true,
        placements: ['header_trailing'],
        appearance: {
          active: { tone: 'highlight' },
          inactive: { tone: 'muted' },
        },
      },
    }).value!;
    const second = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'second',
      label: 'Second',
      action_id: 'second',
      dialog: { kind: 'none' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.second',
        active_value: true,
        placements: ['header_trailing', 'actions_bar'],
        appearance: {
          active: { tone: 'primary' },
          inactive: { tone: 'muted' },
        },
      },
    }).value!;

    expect(
      selectSessionListRichActionForPlacement(
        [first, second],
        'header_trailing',
      )?.id,
    ).toBe('first');
    expect(
      selectSessionListRichActionForPlacement([first, second], 'header_leading'),
    ).toBeNull();
  });

  it('evaluates rich state, default pins, and immediate list selection', () => {
    const toggle = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'toggle',
      label: 'Toggle',
      action_id: 'toggle',
      dialog: { kind: 'none' },
      rich_ui: {
        kind: 'toggle',
        value_path: 'metadata.enabled',
        missing_value: false,
        active_value: true,
        default_pinned: true,
        appearance: {
          active: { tone: 'warning' },
          inactive: { tone: 'muted' },
        },
      },
    }).value!;
    const status = normalizeSessionListActionElement({
      ui_type: 'session_list_action',
      plugin: 'fixture',
      id: 'status',
      label: 'Status',
      action_id: 'status',
      dialog: { kind: 'form', inputs: [{ name: 'status' }] },
      rich_ui: {
        kind: 'list',
        value_path: 'metadata.status',
        missing_value: 'todo',
        input_name: 'status',
        options: [
          { value: 'todo', label: 'To do', tone: 'muted' },
          { value: 'done', label: 'Done', tone: 'success' },
        ],
      },
    }).value!;
    const summary: SessionSummary = {
      session_id: 'session',
      modified: 1,
      preview: '',
      metadata: { enabled: true },
    };

    expect(resolveSessionListRichActionState(toggle, summary)).toMatchObject({
      kind: 'toggle',
      active: true,
      tone: 'warning',
    });
    const listState = resolveSessionListRichActionState(status, summary);
    expect(listState).toMatchObject({
      kind: 'list',
      value: 'todo',
      currentOption: { value: 'todo', label: 'To do', tone: 'muted' },
    });
    expect(getDefaultPinnedSessionListActionKeys([toggle, status])).toEqual(['toggle']);
    const richUi = status.rich_ui;
    expect(richUi?.kind).toBe('list');
    expect(
      buildSessionListRichListDialogValues(
        richUi as any,
        listState && listState.kind === 'list' ? listState.value : undefined,
        'todo',
      ),
    ).toBeNull();
    expect(
      buildSessionListRichListDialogValues(
        richUi as any,
        listState && listState.kind === 'list' ? listState.value : undefined,
        'done',
      ),
    ).toEqual({ status: 'done' });
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