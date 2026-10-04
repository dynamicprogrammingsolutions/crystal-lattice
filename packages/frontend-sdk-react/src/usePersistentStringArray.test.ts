import { describe, expect, it } from 'vitest';

import {
  parsePersistentStringArray,
  resolveDefaultPersistentStringArray,
} from './usePersistentStringArray';

describe('persistent string-array preference semantics', () => {
  it('treats a stored empty array as an authoritative preference', () => {
    expect(parsePersistentStringArray('[]')).toEqual([]);
    expect(
      resolveDefaultPersistentStringArray({
        current: [],
        initial: ['toggle_session_pinned', 'toggle_session_archived'],
        hasStoredPreference: true,
      }),
    ).toEqual([]);
  });

  it('applies newly declared defaults only while storage is absent', () => {
    expect(
      resolveDefaultPersistentStringArray({
        current: ['agentSwitch', 'settings'],
        initial: [
          'agentSwitch',
          'settings',
          'toggle_session_pinned',
          'toggle_session_archived',
        ],
        hasStoredPreference: false,
      }),
    ).toEqual([
      'agentSwitch',
      'settings',
      'toggle_session_pinned',
      'toggle_session_archived',
    ]);
  });

  it('rejects malformed stored values so a default can be used', () => {
    expect(parsePersistentStringArray('{"not":"an array"}')).toBeNull();
    expect(parsePersistentStringArray('[1, "pin", null]')).toEqual(['pin']);
  });

  it('keeps an explicit user choice when plugin defaults move from pin to status', () => {
    expect(
      resolveDefaultPersistentStringArray({
        current: ['toggle_session_pinned'],
        initial: ['set_session_status'],
        hasStoredPreference: true,
      }),
    ).toEqual(['toggle_session_pinned']);
    expect(
      resolveDefaultPersistentStringArray({
        current: [],
        initial: ['set_session_status'],
        hasStoredPreference: true,
      }),
    ).toEqual([]);
    expect(
      resolveDefaultPersistentStringArray({
        current: ['toggle_session_pinned'],
        initial: ['set_session_status'],
        hasStoredPreference: false,
      }),
    ).toEqual(['set_session_status']);
  });
});