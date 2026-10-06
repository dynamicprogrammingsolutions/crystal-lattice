export interface AgentPluginEntry {
  id: string;
  kind: 'providers' | 'extensions' | 'features' | 'tools' | (string & {});
  name?: string;
  class_path?: string;
  class_name?: string;
  enabled: boolean;
  source?: 'agent' | 'implicit' | (string & {});
  active: boolean;
}

export function normalizeAgentPluginEntries(
  values: readonly unknown[] | null | undefined,
): AgentPluginEntry[] {
  if (!Array.isArray(values)) return [];

  return values.flatMap(value => {
    if (!value || typeof value !== 'object') return [];
    const candidate = value as Record<string, unknown>;
    const id = typeof candidate.id === 'string' ? candidate.id.trim() : '';
    const kind =
      typeof candidate.kind === 'string' ? candidate.kind.trim() : '';
    if (!id || !kind) return [];

    const entry: AgentPluginEntry = {
      id,
      kind,
      enabled: candidate.enabled === true,
      active: candidate.active === true,
    };
    if (typeof candidate.name === 'string' && candidate.name.trim()) {
      entry.name = candidate.name.trim();
    }
    if (
      typeof candidate.class_path === 'string' &&
      candidate.class_path.trim()
    ) {
      entry.class_path = candidate.class_path.trim();
    }
    if (
      typeof candidate.class_name === 'string' &&
      candidate.class_name.trim()
    ) {
      entry.class_name = candidate.class_name.trim();
    }
    if (typeof candidate.source === 'string' && candidate.source.trim()) {
      entry.source = candidate.source.trim();
    }
    return [entry];
  });
}