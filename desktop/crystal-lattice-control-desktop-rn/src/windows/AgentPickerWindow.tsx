import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  ThemeProvider,
  useTheme,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';
import {
  AgentsController,
  normalizeAgentDescriptors,
  type AgentBackend,
  type AgentDescriptor,
  type AgentPluginEntry,
} from '@crystal-lattice/frontend-sdk';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import {
  clearActiveAgentPickerWindow,
  useActiveAgentPickerWindow,
} from './agentPickerCoordinator';
import { DesktopWindowManager } from './desktopWindowManager';

const KIND_ORDER = ['providers', 'extensions', 'features', 'tools'] as const;
type PluginKind = (typeof KIND_ORDER)[number];

const KIND_LABELS: Record<PluginKind, string> = {
  providers: 'Provider',
  extensions: 'Extensions',
  features: 'Features',
  tools: 'Tools',
};

type PluginPreviewState =
  | { status: 'idle'; plugins: AgentPluginEntry[] }
  | { status: 'loading'; plugins: AgentPluginEntry[] }
  | { status: 'ready'; plugins: AgentPluginEntry[] }
  | { status: 'unavailable'; plugins: AgentPluginEntry[] }
  | { status: 'error'; plugins: AgentPluginEntry[] };

export interface AgentPickerWindowProps {
  connectionId: string;
  connectionName?: string;
  agents?: string[];
  agentDescriptors?: AgentDescriptor[];
  backend?: AgentBackend;
  themeOverride?: Theme;
  mode?: 'createSession' | 'switchSessionAgent';
  sessionId?: string;
  title?: string;
  primaryButtonLabel?: string;
  initialAgentId?: string;
}

function humanizePluginLabel(plugin: AgentPluginEntry): string {
  const raw =
    (typeof plugin.name === 'string' && plugin.name.trim()) ||
    (typeof plugin.class_name === 'string' && plugin.class_name.trim()) ||
    plugin.id;
  return raw
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function coercePluginKind(kind: string): PluginKind | null {
  return KIND_ORDER.includes(kind as PluginKind) ? (kind as PluginKind) : null;
}

export function AgentPickerWindow(
  props: AgentPickerWindowProps,
): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={props.themeOverride ?? systemTheme}>
      <AgentPickerWindowInner {...props} />
    </ThemeProvider>
  );
}

function AgentPickerWindowInner({
  connectionId,
  connectionName,
  agents,
  agentDescriptors,
  backend: backendProp,
  mode = 'createSession',
  sessionId,
  title,
  primaryButtonLabel,
  initialAgentId,
}: AgentPickerWindowProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveAgentPickerWindow();
  const backend =
    backendProp ??
    (active?.connectionId === connectionId ? active.backend : null);

  const descriptorList = useMemo(() => {
    const normalized = normalizeAgentDescriptors(agentDescriptors);
    if (normalized.length > 0) {
      return normalized;
    }
    return (Array.isArray(agents) ? agents : []).map((id, index) => ({
      id,
      title: id,
      description: '',
      order: index,
    }));
  }, [agentDescriptors, agents]);
  const agentList = descriptorList.map(descriptor => descriptor.id);
  const initialSelected = useMemo(() => {
    if (
      typeof initialAgentId === 'string' &&
      initialAgentId &&
      agentList.includes(initialAgentId)
    ) {
      return initialAgentId;
    }
    return agentList[0] ?? null;
  }, [agentList, initialAgentId]);

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(
    initialSelected,
  );
  const [pluginPreview, setPluginPreview] = useState<PluginPreviewState>({
    status: 'idle',
    plugins: [],
  });
  const [retryRevision, setRetryRevision] = useState(0);
  const [expandedKinds, setExpandedKinds] = useState<Record<PluginKind, boolean>>(
    {
      providers: false,
      extensions: false,
      features: false,
      tools: true,
    },
  );

  const controller = useMemo(
    () => new AgentsController({ backend, cacheKey: connectionId }),
    [backend, connectionId],
  );
  const selectedDescriptor = useMemo(
    () =>
      descriptorList.find(descriptor => descriptor.id === selectedAgentId) ??
      null,
    [descriptorList, selectedAgentId],
  );

  useEffect(() => {
    if (!selectedAgentId) {
      setPluginPreview({ status: 'idle', plugins: [] });
      return;
    }
    if (!backend || !backend.listAgentPlugins) {
      setPluginPreview({ status: 'unavailable', plugins: [] });
      return;
    }

    let current = true;
    setPluginPreview({ status: 'loading', plugins: [] });
    controller
      .ensurePluginsLoaded(selectedAgentId)
      .then(plugins => {
        if (current) {
          setPluginPreview({ status: 'ready', plugins });
        }
      })
      .catch(() => {
        if (current) {
          setPluginPreview({ status: 'error', plugins: [] });
        }
      });
    return () => {
      current = false;
    };
  }, [backend, controller, retryRevision, selectedAgentId]);

  const groupedPlugins = useMemo(() => {
    const groups: Record<PluginKind, AgentPluginEntry[]> = {
      providers: [],
      extensions: [],
      features: [],
      tools: [],
    };
    pluginPreview.plugins.forEach(plugin => {
      const kind = coercePluginKind(plugin.kind);
      if (kind) {
        groups[kind].push(plugin);
      }
    });
    return groups;
  }, [pluginPreview.plugins]);

  const submit = () => {
    if (!connectionId || !selectedAgentId) {
      return;
    }
    clearActiveAgentPickerWindow();
    DesktopWindowManager?.submitAgentPicker({
      connectionId,
      agentId: selectedAgentId,
      mode,
      sessionId: mode === 'switchSessionAgent' ? sessionId : undefined,
    });
  };

  const cancel = () => {
    clearActiveAgentPickerWindow();
    DesktopWindowManager?.cancelAgentPicker();
  };

  return (
    <View testID="agent-picker-window" style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>
          {title
            ? title
            : mode === 'switchSessionAgent'
              ? 'Switch Agent'
              : 'New Session'}
        </Text>
        <Text style={styles.subtitle} numberOfLines={1}>
          {connectionName
            ? `Connection: ${connectionName}`
            : `Connection: ${connectionId}`}
        </Text>
        {mode === 'switchSessionAgent' && sessionId ? (
          <Text style={styles.subtitle} numberOfLines={1}>
            Session: {sessionId}
          </Text>
        ) : null}
      </View>

      {agentList.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No agents available.</Text>
          <Text style={styles.emptyMeta}>
            Open the connection and try again.
          </Text>
        </View>
      ) : (
        <View style={styles.panes}>
          <ScrollView
            style={styles.list}
            contentContainerStyle={styles.listContent}
          >
            {descriptorList.map(descriptor => {
              const agentId = descriptor.id;
              const selected = selectedAgentId === agentId;
              return (
                <Pressable
                  key={agentId}
                  testID={`agent-picker-row-${agentId}`}
                  style={state => {
                    const hovered = (state as any).hovered as
                      | boolean
                      | undefined;
                    return [
                      styles.row,
                      selected && styles.rowSelected,
                      (hovered || state.pressed) && styles.rowHovered,
                    ];
                  }}
                  onPress={() => setSelectedAgentId(agentId)}
                  accessibilityLabel={`${descriptor.title}. ${
                    descriptor.description || agentId
                  }`}
                  accessibilityState={{ selected }}
                >
                  <View style={styles.rowCopy}>
                    <Text style={styles.rowText} numberOfLines={1}>
                      {descriptor.title}
                    </Text>
                    {descriptor.description ? (
                      <Text
                        style={styles.rowDescription}
                        numberOfLines={2}
                      >
                        {descriptor.description}
                      </Text>
                    ) : null}
                    {descriptor.title !== agentId ? (
                      <Text style={styles.rowId} numberOfLines={1}>
                        {agentId}
                      </Text>
                    ) : null}
                  </View>
                  {selected ? <Text style={styles.check}>✓</Text> : null}
                </Pressable>
              );
            })}
          </ScrollView>

          <View testID="agent-defaults-pane" style={styles.detailsPane}>
            <View style={styles.detailsHeader}>
              <Text style={styles.detailsEyebrow}>
                {mode === 'switchSessionAgent'
                  ? 'Target agent defaults'
                  : 'Agent defaults'}
              </Text>
              <Text style={styles.detailsTitle} numberOfLines={1}>
                {selectedDescriptor?.title ?? selectedAgentId ?? 'Select an agent'}
              </Text>
              {selectedDescriptor?.description ? (
                <Text style={styles.detailsDescription} numberOfLines={2}>
                  {selectedDescriptor.description}
                </Text>
              ) : null}
              {selectedDescriptor?.id ? (
                <Text style={styles.detailsId} numberOfLines={1}>
                  {selectedDescriptor.id}
                </Text>
              ) : null}
            </View>

            {pluginPreview.status === 'loading' ? (
              <View style={styles.previewMessage}>
                <ActivityIndicator size="small" color={theme.primary} />
                <Text style={styles.previewMessageText}>
                  Loading effective defaults…
                </Text>
              </View>
            ) : null}

            {pluginPreview.status === 'unavailable' ? (
              <View style={styles.previewMessage}>
                <Text style={styles.previewMessageTitle}>
                  Plugin preview unavailable
                </Text>
                <Text style={styles.previewMessageText}>
                  You can still select this agent. Reconnect to a current
                  Crystal Lattice server to preview its defaults.
                </Text>
              </View>
            ) : null}

            {pluginPreview.status === 'error' ? (
              <View style={styles.previewMessage}>
                <Text style={styles.previewMessageTitle}>
                  Agent defaults could not be loaded
                </Text>
                <Text style={styles.previewMessageText}>
                  You can still select this agent.
                </Text>
                <Pressable
                  style={styles.retryButton}
                  onPress={() => setRetryRevision(value => value + 1)}
                >
                  <Text style={styles.retryButtonText}>Try again</Text>
                </Pressable>
              </View>
            ) : null}

            {pluginPreview.status === 'ready' ? (
              <ScrollView
                style={styles.pluginList}
                contentContainerStyle={styles.pluginListContent}
              >
                {KIND_ORDER.map(kind => {
                  const entries = groupedPlugins[kind];
                  const expanded = expandedKinds[kind];
                  return (
                    <View key={kind} style={styles.pluginSection}>
                      <Pressable
                        testID={`agent-plugin-group-${kind}`}
                        style={styles.pluginSectionHeader}
                        onPress={() =>
                          setExpandedKinds(current => ({
                            ...current,
                            [kind]: !current[kind],
                          }))
                        }
                        accessibilityLabel={`${KIND_LABELS[kind]}, ${entries.length} plugins`}
                        accessibilityState={{ expanded }}
                      >
                        <Text style={styles.pluginSectionDisclosure}>
                          {expanded ? '▾' : '▸'}
                        </Text>
                        <Text style={styles.pluginSectionTitle}>
                          {KIND_LABELS[kind]}
                        </Text>
                        <Text style={styles.pluginSectionCount}>
                          {entries.length}
                        </Text>
                      </Pressable>

                      {expanded ? (
                        entries.length > 0 ? (
                          <View style={styles.pluginRows}>
                            {entries.map(plugin => {
                              const label = humanizePluginLabel(plugin);
                              const status = !plugin.enabled
                                ? 'Disabled'
                                : !plugin.active
                                  ? 'Inactive'
                                  : 'Default';
                              return (
                                <View
                                  key={`${kind}:${plugin.id}:${
                                    plugin.class_path ?? ''
                                  }`}
                                  style={styles.pluginRow}
                                >
                                  <View style={styles.pluginCopy}>
                                    <Text
                                      style={styles.pluginName}
                                      numberOfLines={1}
                                    >
                                      {label}
                                    </Text>
                                    {label.toLowerCase() !==
                                    plugin.id.toLowerCase() ? (
                                      <Text
                                        style={styles.pluginId}
                                        numberOfLines={1}
                                      >
                                        {plugin.id}
                                      </Text>
                                    ) : null}
                                  </View>
                                  <Text
                                    style={[
                                      styles.pluginStatus,
                                      status === 'Disabled' &&
                                        styles.pluginStatusDisabled,
                                      status === 'Inactive' &&
                                        styles.pluginStatusInactive,
                                    ]}
                                  >
                                    {status}
                                  </Text>
                                </View>
                              );
                            })}
                          </View>
                        ) : (
                          <Text style={styles.noPlugins}>
                            No {KIND_LABELS[kind].toLowerCase()} configured.
                          </Text>
                        )
                      ) : null}
                    </View>
                  );
                })}
              </ScrollView>
            ) : null}
          </View>
        </View>
      )}

      <View style={styles.footer}>
        <Pressable
          style={state => [
            styles.button,
            styles.cancelButton,
            state.pressed && styles.buttonPressed,
          ]}
          onPress={cancel}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </Pressable>

        <Pressable
          style={state => {
            const disabled = !selectedAgentId;
            return [
              styles.button,
              styles.createButton,
              disabled && styles.createButtonDisabled,
              state.pressed && !disabled && styles.buttonPressed,
            ];
          }}
          disabled={!selectedAgentId}
          onPress={submit}
        >
          <Text style={styles.createButtonText}>
            {primaryButtonLabel
              ? primaryButtonLabel
              : mode === 'switchSessionAgent'
                ? 'Switch'
                : 'Create'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 18,
      gap: 14,
      backgroundColor: theme.background,
    },
    header: {
      gap: 4,
    },
    title: {
      fontSize: 18,
      fontWeight: '800',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    panes: {
      flex: 1,
      flexDirection: 'row',
      gap: 12,
      minHeight: 0,
    },
    list: {
      width: 320,
      minWidth: 260,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    listContent: {
      paddingVertical: 6,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    rowSelected: {
      backgroundColor: theme.primaryMuted,
    },
    rowText: {
      fontSize: 14,
      color: theme.text,
      fontWeight: '700',
    },
    rowCopy: {
      flex: 1,
      gap: 3,
    },
    rowDescription: {
      fontSize: 12,
      lineHeight: 16,
      color: theme.textSecondary,
    },
    rowId: {
      fontSize: 10,
      color: theme.textMuted,
      fontFamily: 'Menlo',
    },
    check: {
      fontSize: 14,
      fontWeight: '800',
      color: theme.success,
      marginLeft: 8,
    },
    detailsPane: {
      flex: 1,
      minWidth: 0,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    detailsHeader: {
      paddingHorizontal: 14,
      paddingVertical: 12,
      gap: 3,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
    },
    detailsEyebrow: {
      color: theme.primary,
      fontSize: 11,
      fontWeight: '800',
      textTransform: 'uppercase',
      letterSpacing: 0.7,
    },
    detailsTitle: {
      color: theme.text,
      fontSize: 16,
      fontWeight: '800',
    },
    detailsDescription: {
      color: theme.textSecondary,
      fontSize: 12,
      lineHeight: 16,
    },
    detailsId: {
      color: theme.textMuted,
      fontSize: 10,
      fontFamily: 'Menlo',
    },
    previewMessage: {
      padding: 16,
      gap: 8,
      alignItems: 'flex-start',
    },
    previewMessageTitle: {
      color: theme.text,
      fontSize: 13,
      fontWeight: '700',
    },
    previewMessageText: {
      color: theme.textSecondary,
      fontSize: 12,
      lineHeight: 17,
    },
    retryButton: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
      paddingHorizontal: 10,
      paddingVertical: 7,
    },
    retryButtonText: {
      color: theme.text,
      fontSize: 12,
      fontWeight: '700',
    },
    pluginList: {
      flex: 1,
    },
    pluginListContent: {
      padding: 12,
      gap: 8,
    },
    pluginSection: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 9,
      overflow: 'hidden',
    },
    pluginSectionHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      minHeight: 36,
      paddingHorizontal: 10,
      backgroundColor: theme.surfaceAlt,
    },
    pluginSectionDisclosure: {
      width: 18,
      color: theme.textSecondary,
      fontSize: 12,
    },
    pluginSectionTitle: {
      flex: 1,
      color: theme.text,
      fontSize: 12,
      fontWeight: '800',
    },
    pluginSectionCount: {
      color: theme.textMuted,
      fontSize: 11,
      fontVariant: ['tabular-nums'],
    },
    pluginRows: {
      paddingHorizontal: 10,
      paddingVertical: 4,
    },
    pluginRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
      paddingVertical: 7,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
    },
    pluginCopy: {
      flex: 1,
      minWidth: 0,
      gap: 2,
    },
    pluginName: {
      color: theme.text,
      fontSize: 12,
      fontWeight: '700',
    },
    pluginId: {
      color: theme.textMuted,
      fontSize: 10,
      fontFamily: 'Menlo',
    },
    pluginStatus: {
      color: theme.success,
      fontSize: 10,
      fontWeight: '700',
    },
    pluginStatusDisabled: {
      color: theme.textMuted,
    },
    pluginStatusInactive: {
      color: theme.warning,
    },
    noPlugins: {
      color: theme.textMuted,
      fontSize: 11,
      paddingHorizontal: 10,
      paddingVertical: 9,
    },
    empty: {
      padding: 12,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      gap: 4,
    },
    emptyText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: 11,
      color: theme.textMuted,
    },
    footer: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      marginTop: 'auto',
    },
    button: {
      paddingHorizontal: 14,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth,
    },
    buttonPressed: {
      opacity: 0.85,
    },
    cancelButton: {
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    cancelButtonText: {
      color: theme.text,
      fontWeight: '700',
      fontSize: 12,
    },
    createButton: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    createButtonDisabled: {
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    createButtonText: {
      color: theme.textOnPrimary,
      fontWeight: '800',
      fontSize: 12,
    },
  });
}