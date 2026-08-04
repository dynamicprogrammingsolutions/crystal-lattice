import { describe, expect, it } from 'vitest';

import {
  applicationActionKey,
  buildApplicationActionsByKey,
  normalizeApplicationActionElements,
} from './applicationActions';

describe('application actions', () => {
  it('keeps action identity scoped by plugin', () => {
    const byKey = buildApplicationActionsByKey([
      { plugin: 'first', id: 'reload', inputs: { first: { type: 'string' } } },
      { plugin: 'second', id: 'reload', inputs: { second: { type: 'string' } } },
    ]);

    expect(byKey[applicationActionKey('first', 'reload')]?.inputs).toHaveProperty('first');
    expect(byKey[applicationActionKey('second', 'reload')]?.inputs).toHaveProperty('second');
  });

  it('normalizes ordered screen-independent declarations', () => {
    const actionsByKey = buildApplicationActionsByKey([
      { plugin: 'config', id: 'reload' },
      { plugin: 'config', id: 'credential' },
    ]);
    const normalized = normalizeApplicationActionElements({
      actionsByKey,
      elements: [
        {
          ui_type: 'application_action',
          plugin: 'config',
          id: 'credential-button',
          action_id: 'credential',
          label: 'Credential',
          order: 20,
        },
        {
          ui_type: 'application_action',
          plugin: 'config',
          id: 'reload-button',
          action_id: 'reload',
          label: 'Reload',
          order: 10,
        },
      ],
    });

    expect(normalized.diagnostics).toEqual([]);
    expect(normalized.actions.map((action) => action.id)).toEqual([
      'reload-button',
      'credential-button',
    ]);
  });
});