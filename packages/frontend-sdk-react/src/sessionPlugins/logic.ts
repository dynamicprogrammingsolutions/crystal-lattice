import type { SessionPluginEntry } from '@crystal-lattice/frontend-sdk';

export function computeEnabledIds(plugins: readonly SessionPluginEntry[]): string[] {
  const enabled = new Set<string>();
  for (const plugin of plugins) {
    if (!plugin || typeof plugin.id !== 'string' || !plugin.id) {
      continue;
    }
    if (plugin.enabled) {
      enabled.add(plugin.id);
    }
  }
  return Array.from(enabled);
}

export function computeNextEnabledIds(params: {
  plugins: readonly SessionPluginEntry[];
  pluginId: string;
  nextEnabled: boolean;
}): string[] {
  const { plugins, pluginId, nextEnabled } = params;

  const enabled = new Set<string>(computeEnabledIds(plugins));
  if (typeof pluginId === 'string' && pluginId) {
    if (nextEnabled) {
      enabled.add(pluginId);
    } else {
      enabled.delete(pluginId);
    }
  }
  return Array.from(enabled);
}
