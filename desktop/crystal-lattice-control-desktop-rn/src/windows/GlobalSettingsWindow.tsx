import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  MARKDOWN_BASE_FONT_SIZE_OPTIONS,
  MARKDOWN_HEADER_SIZE_OPTIONS,
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import {
  DEFAULT_DESKTOP_GLOBAL_SETTINGS,
  normalizeDesktopGlobalSettings,
  type DesktopGlobalSettings,
} from '../settings/desktopGlobalSettings';
import { useDesktopTheme } from '../theme/useDesktopTheme';
import { MacSelect } from '../native/MacSelect';
import {
  desktopWindowEvents,
  DesktopWindowManager,
} from './desktopWindowManager';
import {
  desktopHumanTimeDiagnosticsBridge,
  type DesktopHumanTimeDiagnosticEntry,
} from '../humanTimeTelemetry/desktopHumanTimeDiagnostics';

const RECENT_OPTIONS = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '3d', label: 'Last 3 days' },
  { value: '1w', label: 'Last week' },
];

const DOUBLE_CLICK_OPTIONS = [
  { value: 'preview', label: 'Preview session' },
  { value: 'open', label: 'Open permanent tab' },
];

const FOLLOW_ACTIVE_TAB_OPTIONS = [
  { value: 'off', label: 'Off' },
  { value: 'on', label: 'On' },
];

const TIME_TRACKING_INACTIVITY_OPTIONS = [
  { value: '10', label: '10 seconds' },
  { value: '30', label: '30 seconds' },
  { value: '60', label: '1 minute' },
  { value: '120', label: '2 minutes' },
  { value: '300', label: '5 minutes' },
];

function uploadLabel(outcome: string | undefined): string {
  switch (outcome) {
    case 'uploading':
      return 'Uploading';
    case 'flushed':
      return 'Successful';
    case 'partial-failure':
      return 'Some entries rejected';
    case 'transient-failure':
      return 'Waiting to retry';
    case 'definitive-failure':
      return 'Configuration error';
    default:
      return 'Never attempted';
  }
}

function spanLabel(
  value: { connectionId: string; span: { sessionId: string | null } } | null,
): string {
  if (!value) return 'None';
  return `${value.connectionId} / ${
    value.span.sessionId === null ? 'List' : value.span.sessionId
  }`;
}

function entryDurationLabel(entry: DesktopHumanTimeDiagnosticEntry): string {
  const durationMs = Math.max(0, Date.parse(entry.to) - Date.parse(entry.from));
  if (!Number.isFinite(durationMs)) return '—';
  if (durationMs < 1_000) return `${durationMs}ms`;
  const seconds = Math.round(durationMs / 1_000);
  return seconds < 60
    ? `${seconds}s`
    : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

function entryTimeLabel(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toISOString().slice(5, 19).replace('T', ' ');
}

type DesktopGlobalSettingKey =
  | 'baseFontSize'
  | 'headerSize'
  | 'recentSessionsWindow'
  | 'sessionDoubleClickAction'
  | 'sessionsFollowActiveTabEnabled'
  | 'switchConnectionWithActiveTabEnabled'
  | 'timeTrackingEnabled'
  | 'timeTrackingPluginId'
  | 'timeTrackingInactivitySeconds';

export function applyDesktopGlobalSettingChange(
  current: DesktopGlobalSettings,
  key: DesktopGlobalSettingKey,
  value: string | number | boolean,
  write: (params: {
    key: DesktopGlobalSettingKey;
    value: string | number | boolean;
  }) => void,
): DesktopGlobalSettings {
  write({ key, value });
  return normalizeDesktopGlobalSettings({ ...current, [key]: value });
}

export function GlobalSettingsWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <GlobalSettingsWindowInner />
    </ThemeProvider>
  );
}

function GlobalSettingsWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [settings, setSettings] = useState<DesktopGlobalSettings>(
    DEFAULT_DESKTOP_GLOBAL_SETTINGS,
  );
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [diagnosticsBusy, setDiagnosticsBusy] = useState(false);
  const [diagnostics, setDiagnostics] = useState(
    desktopHumanTimeDiagnosticsBridge.getSnapshot(),
  );

  useEffect(() => {
    let cancelled = false;
    DesktopWindowManager?.getDesktopGlobalSettings?.()
      .then(value => {
        if (!cancelled) setSettings(normalizeDesktopGlobalSettings(value));
      })
      .catch(() => {});
    if (!desktopWindowEvents) {
      return () => {
        cancelled = true;
      };
    }
    const subscriptions = [
      desktopWindowEvents.addListener(
        'markdownBaseFontSizeChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              baseFontSize: payload?.baseFontSize,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'markdownHeaderSizeChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              headerSize: payload?.headerSize,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'recentSessionsWindowChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              recentSessionsWindow: payload?.recentSessionsWindow,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'sessionDoubleClickActionChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              sessionDoubleClickAction: payload?.sessionDoubleClickAction,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'sessionsFollowActiveTabChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              sessionsFollowActiveTabEnabled: payload?.enabled === true,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'switchConnectionWithActiveTabChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              switchConnectionWithActiveTabEnabled: payload?.enabled === true,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'timeTrackingEnabledChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              timeTrackingEnabled: payload?.enabled === true,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'timeTrackingPluginIdChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              timeTrackingPluginId: payload?.pluginId,
            }),
          );
        },
      ),
      desktopWindowEvents.addListener(
        'timeTrackingInactivitySecondsChanged',
        (payload: any) => {
          setSettings(current =>
            normalizeDesktopGlobalSettings({
              ...current,
              timeTrackingInactivitySeconds: payload?.seconds,
            }),
          );
        },
      ),
    ];
    return () => {
      cancelled = true;
      subscriptions.forEach(subscription => subscription.remove());
    };
  }, []);

  useEffect(
    () => desktopHumanTimeDiagnosticsBridge.subscribe(setDiagnostics),
    [],
  );

  const update = useCallback(
    (key: DesktopGlobalSettingKey, value: string | number | boolean) => {
      setSettings(current =>
        applyDesktopGlobalSettingChange(current, key, value, params =>
          DesktopWindowManager?.setDesktopGlobalSetting?.(params),
        ),
      );
    },
    [],
  );

  return (
    <View style={styles.root} testID="global-settings-window-root">
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Settings</Text>
          <Text style={styles.subtitle}>
            Global display, history, and session navigation preferences
          </Text>
        </View>
        <Pressable
          accessibilityLabel="Close settings"
          style={styles.closeButton}
          onPress={() =>
            DesktopWindowManager?.closeReactWindow({
              windowKey: 'globalSettings',
            })
          }
        >
          <Text style={styles.closeButtonText}>Close</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.section}>
          <SettingRow label="Font size">
            <MacSelect
              testID="global-settings-font-size"
              style={styles.select}
              options={MARKDOWN_BASE_FONT_SIZE_OPTIONS.map(option => ({
                value: String(option.value),
                label: option.label,
              }))}
              selectedValue={String(settings.baseFontSize)}
              onValueChange={value => update('baseFontSize', Number(value))}
            />
          </SettingRow>
          <SettingRow label="Markdown headers">
            <MacSelect
              testID="global-settings-markdown-headers"
              style={styles.select}
              options={MARKDOWN_HEADER_SIZE_OPTIONS.map(option => ({
                value: option.value,
                label: option.label,
              }))}
              selectedValue={settings.headerSize}
              onValueChange={value => update('headerSize', value)}
            />
          </SettingRow>
          <SettingRow label="Recent sessions">
            <MacSelect
              testID="global-settings-recent-sessions"
              style={styles.select}
              options={RECENT_OPTIONS}
              selectedValue={settings.recentSessionsWindow}
              onValueChange={value => update('recentSessionsWindow', value)}
            />
          </SettingRow>
          <SettingRow label="Double-click action">
            <MacSelect
              testID="global-settings-double-click"
              style={styles.select}
              options={DOUBLE_CLICK_OPTIONS}
              selectedValue={settings.sessionDoubleClickAction}
              onValueChange={value => update('sessionDoubleClickAction', value)}
            />
          </SettingRow>
          <SettingRow label="Follow active tab in Sessions">
            <MacSelect
              testID="global-settings-follow-active-tab"
              style={styles.select}
              options={FOLLOW_ACTIVE_TAB_OPTIONS}
              selectedValue={
                settings.sessionsFollowActiveTabEnabled ? 'on' : 'off'
              }
              onValueChange={value =>
                update('sessionsFollowActiveTabEnabled', value === 'on')
              }
            />
          </SettingRow>
          <SettingRow label="Switch connection with active tab">
            <MacSelect
              testID="global-settings-switch-connection-with-active-tab"
              style={styles.select}
              options={FOLLOW_ACTIVE_TAB_OPTIONS}
              selectedValue={
                settings.switchConnectionWithActiveTabEnabled ? 'on' : 'off'
              }
              onValueChange={value =>
                update('switchConnectionWithActiveTabEnabled', value === 'on')
              }
            />
          </SettingRow>
          <SettingRow label="Time tracking">
            <Switch
              testID="global-settings-time-tracking-toggle"
              accessibilityLabel="Time tracking"
              value={settings.timeTrackingEnabled}
              onValueChange={value => update('timeTrackingEnabled', value)}
            />
          </SettingRow>
          <SettingRow label="Telemetry plugin">
            <TextInput
              testID="global-settings-telemetry-plugin-input"
              accessibilityLabel="Telemetry plugin"
              style={styles.pluginInput}
              value={settings.timeTrackingPluginId}
              onChangeText={value => update('timeTrackingPluginId', value)}
              autoCapitalize="none"
              autoCorrect={false}
            />
          </SettingRow>
          <SettingRow label="Maximum inactivity">
            <MacSelect
              testID="global-settings-time-tracking-inactivity"
              style={styles.select}
              options={TIME_TRACKING_INACTIVITY_OPTIONS}
              selectedValue={String(settings.timeTrackingInactivitySeconds)}
              onValueChange={value =>
                update('timeTrackingInactivitySeconds', Number(value))
              }
            />
          </SettingRow>
        </View>

        <Pressable
          testID="global-settings-time-tracking-diagnostics"
          accessibilityRole="button"
          style={styles.diagnosticsToggle}
          onPress={() => {
            const next = !showDiagnostics;
            setShowDiagnostics(next);
            if (next) {
              void desktopHumanTimeDiagnosticsBridge.refresh();
            }
          }}
        >
          <Text style={styles.diagnosticsToggleText}>
            {showDiagnostics ? 'Hide diagnostics' : 'Show diagnostics'}
          </Text>
        </Pressable>

        {showDiagnostics ? (
          <View testID="time-tracking-diagnostics" style={styles.diagnostics}>
            <View
              testID="time-tracking-collection-state"
              accessible
              accessibilityLabel={`Collection: ${
                diagnostics.enabled ? 'Enabled' : 'Disabled'
              }`}
            >
              <Text style={styles.diagnosticsText}>
                Collection: {diagnostics.enabled ? 'Enabled' : 'Disabled'}
              </Text>
            </View>
            <View
              testID="time-tracking-connected-count"
              accessible
              accessibilityLabel={`Connected servers: ${diagnostics.connectedConnectionCount}`}
            >
              <Text style={styles.diagnosticsText}>
                Connected servers: {diagnostics.connectedConnectionCount}
              </Text>
            </View>
            <View
              testID="time-tracking-activity-count"
              accessible
              accessibilityLabel={`Activity events: ${diagnostics.activityEventCount}`}
            >
              <Text style={styles.diagnosticsText}>
                Activity events: {diagnostics.activityEventCount}
              </Text>
            </View>
            <Text style={styles.diagnosticsText}>
              Open span: {spanLabel(diagnostics.openSpan)}
            </Text>
            <View
              testID="time-tracking-last-collected"
              accessible
              accessibilityLabel={`Last collected: ${spanLabel(
                diagnostics.lastCollectedSpan,
              )}`}
            >
              <Text style={styles.diagnosticsText}>
                Last collected: {spanLabel(diagnostics.lastCollectedSpan)}
              </Text>
            </View>
            <Text
              testID="time-tracking-pending-count"
              style={styles.diagnosticsText}
            >
              Pending uploads: {diagnostics.pendingCount}
            </Text>
            <Text
              testID="time-tracking-last-upload"
              style={styles.diagnosticsText}
            >
              Last upload: {uploadLabel(diagnostics.lastUpload?.event.outcome)}
            </Text>
            {diagnostics.lastUpload?.event.result ? (
              <Text style={styles.diagnosticsDetail}>
                Recorded {diagnostics.lastUpload.event.result.recorded}, merged{' '}
                {diagnostics.lastUpload.event.result.merged}, skipped{' '}
                {diagnostics.lastUpload.event.result.skipped}
              </Text>
            ) : null}
            {diagnostics.collectionError ||
            diagnostics.lastUpload?.event.error ? (
              <Text style={styles.diagnosticsError}>
                {diagnostics.collectionError ??
                  diagnostics.lastUpload?.event.error}
              </Text>
            ) : null}

            <Text style={styles.diagnosticsTitle}>Recent entries</Text>
            <View style={styles.tableRow}>
              {[
                'Status',
                'Connection',
                'Session',
                'Time (UTC)',
                'Duration',
              ].map(label => (
                <Text
                  key={label}
                  style={[styles.tableCell, styles.tableHeader]}
                >
                  {label}
                </Text>
              ))}
            </View>
            {diagnostics.recentEntries.length === 0 ? (
              <Text style={styles.diagnosticsDetail}>
                No collected entries.
              </Text>
            ) : (
              diagnostics.recentEntries.map((entry, index) => (
                <View
                  key={`${entry.connectionId}-${entry.sessionId ?? 'list'}-${
                    entry.from
                  }-${entry.to}`}
                  testID={`time-tracking-entry-${index}`}
                  style={styles.tableRow}
                >
                  <Text style={styles.tableCell}>{entry.uploadStatus}</Text>
                  <Text selectable numberOfLines={1} style={styles.tableCell}>
                    {entry.connectionId}
                  </Text>
                  <Text selectable numberOfLines={1} style={styles.tableCell}>
                    {entry.sessionId ?? 'List'}
                  </Text>
                  <Text numberOfLines={1} style={styles.tableCell}>
                    {entryTimeLabel(entry.to)}
                  </Text>
                  <Text style={styles.tableCell}>
                    {entryDurationLabel(entry)}
                  </Text>
                </View>
              ))
            )}
            <View style={styles.diagnosticsActions}>
              <Pressable
                testID="time-tracking-upload-now"
                accessibilityRole="button"
                accessibilityLabel="Upload human time now"
                disabled={diagnosticsBusy}
                style={styles.diagnosticsButton}
                onPress={() => {
                  setDiagnosticsBusy(true);
                  void desktopHumanTimeDiagnosticsBridge
                    .uploadNow()
                    .finally(() => setDiagnosticsBusy(false));
                }}
              >
                <Text style={styles.diagnosticsButtonText}>Upload now</Text>
              </Pressable>
              <Pressable
                testID="time-tracking-refresh-diagnostics"
                accessibilityRole="button"
                accessibilityLabel="Refresh human time diagnostics"
                disabled={diagnosticsBusy}
                style={styles.diagnosticsButton}
                onPress={() => {
                  setDiagnosticsBusy(true);
                  void desktopHumanTimeDiagnosticsBridge
                    .refresh()
                    .finally(() => setDiagnosticsBusy(false));
                }}
              >
                <Text style={styles.diagnosticsButtonText}>Refresh</Text>
              </Pressable>
            </View>
          </View>
        ) : null}
      </ScrollView>
    </View>
  );
}

function SettingRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      {children}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 20,
      gap: 18,
      backgroundColor: theme.background,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: 16,
    },
    headerText: {
      gap: 4,
      flex: 1,
    },
    title: {
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: '700',
      color: theme.text,
    },
    subtitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    closeButton: {
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      paddingHorizontal: 12,
      paddingVertical: 7,
      backgroundColor: theme.surface,
    },
    closeButtonText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.text,
      fontWeight: '600',
    },
    section: {
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    scrollContent: {
      gap: 14,
      paddingBottom: 20,
    },
    row: {
      minHeight: 52,
      paddingHorizontal: 14,
      paddingVertical: 9,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 16,
    },
    rowLabel: {
      flex: 1,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
      fontWeight: '600',
    },
    select: {
      width: 210,
      minHeight: 30,
    },
    pluginInput: {
      width: 260,
      minHeight: 30,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 6,
      paddingHorizontal: 10,
      paddingVertical: 6,
      color: theme.text,
      backgroundColor: theme.background,
    },
    diagnosticsToggle: {
      alignSelf: 'flex-start',
      paddingVertical: 4,
    },
    diagnosticsToggleText: {
      color: theme.primary,
      fontWeight: '600',
    },
    diagnostics: {
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      padding: 12,
      gap: 5,
    },
    diagnosticsText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
    },
    diagnosticsDetail: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
    },
    diagnosticsError: {
      color: theme.danger,
      fontSize: theme.typography.fontSize.small,
    },
    diagnosticsTitle: {
      marginTop: 8,
      color: theme.text,
      fontWeight: '700',
    },
    tableRow: {
      flexDirection: 'row',
      borderTopWidth: 1,
      borderTopColor: theme.divider,
      paddingVertical: 5,
      gap: 4,
    },
    tableCell: {
      flex: 1,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
    },
    tableHeader: {
      color: theme.text,
      fontWeight: '700',
    },
    diagnosticsActions: {
      flexDirection: 'row',
      gap: 8,
      marginTop: 8,
    },
    diagnosticsButton: {
      borderRadius: 6,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.background,
      paddingHorizontal: 10,
      paddingVertical: 6,
    },
    diagnosticsButtonText: {
      color: theme.text,
      fontWeight: '600',
      fontSize: theme.typography.fontSize.small,
    },
  });
}
