import { describe, expect, it } from 'vitest';

import type { SessionPluginEntry } from '@crystal-lattice/frontend-sdk';

import { computeEnabledIds, computeNextEnabledIds } from './logic';

describe('computeEnabledIds', () => {
  it('returns ids for enabled plugins only', () => {
    const plugins: SessionPluginEntry[] = [
      { id: 'a', kind: 'tools', enabled: true },
      { id: 'b', kind: 'tools', enabled: false },
      { id: 'c', kind: 'features', enabled: true },
    ];

    expect(computeEnabledIds(plugins).sort()).toEqual(['a', 'c']);
  });

  it('ignores invalid entries', () => {
    expect(computeEnabledIds([{ id: '', kind: 'tools', enabled: true }] as any)).toEqual([]);
  });
});

describe('computeNextEnabledIds', () => {
  it('adds plugin id when enabling', () => {
    const plugins: SessionPluginEntry[] = [
      { id: 'a', kind: 'tools', enabled: true },
      { id: 'b', kind: 'tools', enabled: false },
    ];

    const next = computeNextEnabledIds({ plugins, pluginId: 'b', nextEnabled: true });
    expect(next.sort()).toEqual(['a', 'b']);
  });

  it('removes plugin id when disabling', () => {
    const plugins: SessionPluginEntry[] = [
      { id: 'a', kind: 'tools', enabled: true },
      { id: 'b', kind: 'tools', enabled: true },
    ];

    const next = computeNextEnabledIds({ plugins, pluginId: 'b', nextEnabled: false });
    expect(next.sort()).toEqual(['a']);
  });
});
