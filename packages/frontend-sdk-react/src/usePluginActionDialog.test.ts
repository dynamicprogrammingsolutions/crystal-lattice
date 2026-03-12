import { describe, expect, it } from 'vitest';

import { shouldOpenPluginActionDialog } from './usePluginActionDialog';

describe('shouldOpenPluginActionDialog', () => {
  it('returns false when dialog is missing', () => {
    expect(shouldOpenPluginActionDialog(undefined)).toBe(false);
    expect(shouldOpenPluginActionDialog(null)).toBe(false);
  });

  it('returns false when dialog kind is missing or none', () => {
    expect(shouldOpenPluginActionDialog({})).toBe(false);
    expect(shouldOpenPluginActionDialog({ title: 'Action' })).toBe(false);
    expect(shouldOpenPluginActionDialog({ kind: 'none' })).toBe(false);
  });

  it('returns true for supported modal dialogs', () => {
    expect(shouldOpenPluginActionDialog({ kind: 'form', inputs: [] })).toBe(true);
    expect(shouldOpenPluginActionDialog({ kind: 'confirm' })).toBe(true);
  });
});