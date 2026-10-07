import React, { useMemo, useState } from 'react';
import {
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  CODE_BLOCK_RENDERER_OPTIONS,
  MARKDOWN_BASE_FONT_SIZE_OPTIONS,
  MARKDOWN_HEADER_SIZE_OPTIONS,
  MARKDOWN_RENDERER_OPTIONS,
  useMarkdownDisplayPreferences,
  type CodeBlockRendererId,
  type MarkdownBaseFontSize,
  type MarkdownHeaderSize,
  type MarkdownRendererId,
} from '@crystal-lattice/frontend-rn-components';

import OptionsPickerModal, { type OptionItem } from './OptionsPickerModal';
import PanelModalFrame from './PanelModalFrame';
import EmbeddedReviewerSettings from '../embeddedRuntime/EmbeddedReviewerSettings';
import {
  isEmbeddedPythonRuntimeAvailable,
  type EmbeddedRuntimePublicConfiguration,
} from '../embeddedRuntime/embeddedPythonRuntime';
import { useTheme, type Theme } from '../theme';
import { useHomeWorkspace } from '../HomeWorkspaceContext';
import {
  DEFAULT_TIME_TRACKING_PLUGIN_ID,
  type RecentSessionsWindow,
} from '../homeWorkspaceState';
import { resolveMobileMarkdownRendererPreferences } from '../markdownRendererPreferences';
import {
  useHumanTimeTelemetry,
  type HumanTimeDiagnosticUploadStatus,
} from '../humanTimeTelemetry/HumanTimeTelemetryProvider';

interface GlobalSettingsModalProps {
  visible: boolean;
  onRequestClose: () => void;
  onEmbeddedSettingsChanged?: (configuration: EmbeddedRuntimePublicConfiguration) => void;
}

type SettingsPicker =
  | 'font'
  | 'headers'
  | 'markdownRenderer'
  | 'codeRenderer'
  | 'recent';

const RECENT_SESSION_OPTIONS: readonly OptionItem[] = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '3d', label: 'Last 3 days' },
  { value: '1w', label: 'Last week' },
];

function optionItems(picker: SettingsPicker | null): readonly OptionItem[] {
  switch (picker) {
    case 'font':
      return MARKDOWN_BASE_FONT_SIZE_OPTIONS.map((option) => ({
        value: String(option.value),
        label: option.label,
      }));
    case 'headers':
      return MARKDOWN_HEADER_SIZE_OPTIONS.map((option) => ({ ...option }));
    case 'markdownRenderer':
      return MARKDOWN_RENDERER_OPTIONS.map((option) => ({ ...option }));
    case 'codeRenderer':
      return CODE_BLOCK_RENDERER_OPTIONS.map((option) => ({ ...option }));
    case 'recent':
      return RECENT_SESSION_OPTIONS;
    default:
      return [];
  }
}

function optionLabel(
  options: ReadonlyArray<{ value: string; label: string }>,
  value: string,
): string {
  return options.find((option) => option.value === value)?.label ?? value;
}

function spanLabel(sessionId: string | null): string {
  return sessionId === null
    ? 'Sessions list'
    : `Session ${sessionId.slice(0, 8)}`;
}

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

function entryUploadLabel(status: HumanTimeDiagnosticUploadStatus): string {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'uploading':
      return 'Uploading';
    case 'uploaded':
      return 'Uploaded';
    case 'retrying':
      return 'Retrying';
    case 'failed':
      return 'Failed';
  }
}

function entrySessionLabel(sessionId: string | null): string {
  return sessionId === null ? 'List' : sessionId;
}

function entryTimeLabel(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const iso = parsed.toISOString();
  return `${iso.slice(5, 10)} ${iso.slice(11, 19)}`;
}

function entryDurationLabel(from: string, to: string): string {
  const durationMs = Math.max(0, Date.parse(to) - Date.parse(from));
  if (!Number.isFinite(durationMs)) return '—';
  if (durationMs < 1_000) return `${durationMs}ms`;
  const totalSeconds = Math.round(durationMs / 1_000);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds === 0 ? `${minutes}m` : `${minutes}m ${seconds}s`;
}

const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  visible,
  onRequestClose,
  onEmbeddedSettingsChanged,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const { preferences, setPreferences } = useMarkdownDisplayPreferences();
  const {
    recentSessionsWindow,
    setRecentSessionsWindow,
    timeTrackingEnabled,
    timeTrackingPluginId,
    setTimeTrackingEnabled,
    setTimeTrackingPluginId,
  } = useHomeWorkspace();
  const { diagnostics, refreshDiagnostics, uploadNow } =
    useHumanTimeTelemetry();
  const [picker, setPicker] = useState<SettingsPicker | null>(null);
  const [showTimeDiagnostics, setShowTimeDiagnostics] = useState(false);
  const [diagnosticsBusy, setDiagnosticsBusy] = useState(false);
  const options = optionItems(picker);
  const resolvedRenderers =
    resolveMobileMarkdownRendererPreferences(preferences);
  const selectedPickerValue =
    picker === 'font'
      ? String(preferences.baseFontSize)
      : picker === 'headers'
      ? preferences.headerSize
      : picker === 'markdownRenderer'
      ? preferences.markdownRenderer
      : picker === 'codeRenderer'
      ? preferences.codeBlockRenderer
      : picker === 'recent'
      ? recentSessionsWindow
      : '';
  const fallbackMessages = [
    resolvedRenderers.markdownRendererFellBack
      ? `Markdown renderer unavailable; using ${optionLabel(
          MARKDOWN_RENDERER_OPTIONS,
          resolvedRenderers.markdownRenderer,
        )}.`
      : null,
    resolvedRenderers.codeBlockRendererFellBack
      ? `Code renderer unavailable; using ${optionLabel(
          CODE_BLOCK_RENDERER_OPTIONS,
          resolvedRenderers.codeBlockRenderer,
        )}.`
      : null,
  ].filter((message): message is string => message !== null);

  return (
    <PanelModalFrame
      visible={visible}
      title="Settings"
      onRequestClose={onRequestClose}
      contentStyle={styles.modal}
      testID="global-settings-modal"
      scroll
      scrollTestID="global-settings-scroll"
      overlayChildren={
        <OptionsPickerModal
          visible={visible && picker !== null}
          options={options}
          selectedValue={selectedPickerValue}
          useModal={false}
          onRequestClose={() => setPicker(null)}
          onSelect={(value) => {
            switch (picker) {
              case 'font':
                setPreferences((current) => ({
                  ...current,
                  baseFontSize: Number(value) as MarkdownBaseFontSize,
                }));
                break;
              case 'headers':
                setPreferences((current) => ({
                  ...current,
                  headerSize: value as MarkdownHeaderSize,
                }));
                break;
              case 'markdownRenderer':
                setPreferences((current) => ({
                  ...current,
                  markdownRenderer: value as MarkdownRendererId,
                }));
                break;
              case 'codeRenderer':
                setPreferences((current) => ({
                  ...current,
                  codeBlockRenderer: value as CodeBlockRendererId,
                }));
                break;
              case 'recent':
                setRecentSessionsWindow(value as RecentSessionsWindow);
                break;
            }
            setPicker(null);
          }}
        />
      }
    >
      {isEmbeddedPythonRuntimeAvailable() ? (
        <EmbeddedReviewerSettings
          visible={visible}
          onSaved={onEmbeddedSettingsChanged}
        />
      ) : null}
      <View style={styles.settingRow}>
        <Text style={styles.label}>Base font size</Text>
        <TouchableOpacity
          testID="global-settings-base-font-size"
          accessibilityLabel="Base font size"
          style={styles.selector}
          onPress={() => setPicker('font')}
        >
          <Text
            testID="global-settings-base-font-size-value"
            style={styles.selectorText}
          >
            {preferences.baseFontSize}
          </Text>
        </TouchableOpacity>
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.label}>Markdown headers</Text>
        <TouchableOpacity
          testID="global-settings-markdown-headers"
          accessibilityLabel="Markdown headers"
          style={styles.selector}
          onPress={() => setPicker('headers')}
        >
          <Text
            testID="global-settings-markdown-headers-value"
            style={styles.selectorText}
          >
            {preferences.headerSize === 'normal' ? 'Normal' : 'Small'}
          </Text>
        </TouchableOpacity>
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.label}>Markdown renderer</Text>
        <TouchableOpacity
          testID="global-settings-markdown-renderer"
          accessibilityLabel="Markdown renderer"
          style={styles.selector}
          onPress={() => setPicker('markdownRenderer')}
        >
          <Text
            testID="global-settings-markdown-renderer-value"
            style={styles.selectorText}
          >
            {optionLabel(
              MARKDOWN_RENDERER_OPTIONS,
              preferences.markdownRenderer,
            )}
          </Text>
        </TouchableOpacity>
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.label}>Code renderer</Text>
        <TouchableOpacity
          testID="global-settings-code-renderer"
          accessibilityLabel="Code renderer"
          style={styles.selector}
          onPress={() => setPicker('codeRenderer')}
        >
          <Text
            testID="global-settings-code-renderer-value"
            style={styles.selectorText}
          >
            {optionLabel(
              CODE_BLOCK_RENDERER_OPTIONS,
              preferences.codeBlockRenderer,
            )}
          </Text>
        </TouchableOpacity>
      </View>
      {fallbackMessages.map((message) => (
        <Text
          key={message}
          testID="global-settings-renderer-fallback"
          style={styles.fallbackText}
        >
          {message}
        </Text>
      ))}
      <View style={styles.settingRow}>
        <Text style={styles.label}>Recent sessions</Text>
        <TouchableOpacity
          testID="global-settings-recent-sessions"
          accessibilityLabel="Recent sessions"
          style={styles.selector}
          onPress={() => setPicker('recent')}
        >
          <Text
            testID="global-settings-recent-sessions-value"
            style={styles.selectorText}
          >
            {recentSessionsWindow === '24h'
              ? 'Last 24 hours'
              : recentSessionsWindow === '1w'
              ? 'Last week'
              : 'Last 3 days'}
          </Text>
        </TouchableOpacity>
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.label}>Time tracking</Text>
        <Switch
          testID="global-settings-time-tracking-toggle"
          accessibilityLabel="Time tracking"
          value={timeTrackingEnabled}
          onValueChange={(value) => setTimeTrackingEnabled(value)}
        />
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.label}>Telemetry plugin</Text>
        <TextInput
          testID="global-settings-telemetry-plugin-input"
          accessibilityLabel="Telemetry plugin"
          style={styles.pluginInput}
          value={timeTrackingPluginId}
          onChangeText={(value) =>
            setTimeTrackingPluginId(
              value.trim() || DEFAULT_TIME_TRACKING_PLUGIN_ID,
            )
          }
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>
      <TouchableOpacity
        testID="global-settings-time-tracking-diagnostics"
        accessibilityRole="button"
        style={styles.diagnosticsToggle}
        onPress={() => {
          const nextVisible = !showTimeDiagnostics;
          setShowTimeDiagnostics(nextVisible);
          if (nextVisible) {
            void refreshDiagnostics();
          }
        }}
      >
        <Text style={styles.diagnosticsToggleText}>
          {showTimeDiagnostics ? 'Hide diagnostics' : 'Show diagnostics'}
        </Text>
      </TouchableOpacity>
      {showTimeDiagnostics ? (
        <View
          testID="time-tracking-diagnostics"
          style={styles.diagnosticsPanel}
        >
          <Text style={styles.diagnosticsText}>
            Collection: {diagnostics.enabled ? 'Enabled' : 'Disabled'}
          </Text>
          <Text style={styles.diagnosticsText}>
            Connection: {diagnostics.connected ? 'Connected' : 'Disconnected'}
          </Text>
          <Text style={styles.diagnosticsText}>
            Open span:{' '}
            {diagnostics.openSpan
              ? spanLabel(diagnostics.openSpan.sessionId)
              : 'None'}
          </Text>
          <Text style={styles.diagnosticsText}>
            Last collected:{' '}
            {diagnostics.lastCollectedSpan
              ? spanLabel(diagnostics.lastCollectedSpan.sessionId)
              : 'None'}
          </Text>
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
            Last upload: {uploadLabel(diagnostics.lastUpload?.outcome)}
          </Text>
          {diagnostics.lastUpload?.result ? (
            <Text style={styles.diagnosticsDetail}>
              Recorded {diagnostics.lastUpload.result.recorded}, merged{' '}
              {diagnostics.lastUpload.result.merged}, skipped{' '}
              {diagnostics.lastUpload.result.skipped}
            </Text>
          ) : null}
          {diagnostics.collectionError || diagnostics.lastUpload?.error ? (
            <Text style={styles.diagnosticsError}>
              {diagnostics.collectionError ?? diagnostics.lastUpload?.error}
            </Text>
          ) : null}
          <Text style={styles.diagnosticsTableTitle}>Recent entries</Text>
          <View style={styles.diagnosticsTable}>
            <View style={styles.diagnosticsTableRow}>
              <Text
                style={[
                  styles.diagnosticsTableHeader,
                  styles.diagnosticsStatusColumn,
                ]}
              >
                Status
              </Text>
              <Text
                style={[
                  styles.diagnosticsTableHeader,
                  styles.diagnosticsSessionColumn,
                ]}
              >
                Session
              </Text>
              <Text
                style={[
                  styles.diagnosticsTableHeader,
                  styles.diagnosticsTimeColumn,
                ]}
              >
                Time (UTC)
              </Text>
              <Text
                style={[
                  styles.diagnosticsTableHeader,
                  styles.diagnosticsDurationColumn,
                ]}
              >
                Duration
              </Text>
            </View>
            {diagnostics.recentEntries.length === 0 ? (
              <Text style={styles.diagnosticsEmpty}>No collected entries.</Text>
            ) : (
              diagnostics.recentEntries.map((entry, index) => (
                <View
                  key={`${entry.sessionId ?? 'list'}-${entry.from}-${entry.to}`}
                  testID={`time-tracking-entry-${index}`}
                  style={styles.diagnosticsTableRow}
                >
                  <Text
                    style={[
                      styles.diagnosticsTableCell,
                      styles.diagnosticsStatusColumn,
                    ]}
                  >
                    {entryUploadLabel(entry.uploadStatus)}
                  </Text>
                  <Text
                    selectable
                    numberOfLines={1}
                    style={[
                      styles.diagnosticsTableCell,
                      styles.diagnosticsSessionColumn,
                    ]}
                  >
                    {entrySessionLabel(entry.sessionId)}
                  </Text>
                  <Text
                    numberOfLines={1}
                    style={[
                      styles.diagnosticsTableCell,
                      styles.diagnosticsTimeColumn,
                    ]}
                  >
                    {entryTimeLabel(entry.to)}
                  </Text>
                  <Text
                    style={[
                      styles.diagnosticsTableCell,
                      styles.diagnosticsDurationColumn,
                    ]}
                  >
                    {entryDurationLabel(entry.from, entry.to)}
                  </Text>
                </View>
              ))
            )}
          </View>
          <View style={styles.diagnosticsActions}>
            <TouchableOpacity
              testID="time-tracking-upload-now"
              accessibilityRole="button"
              disabled={diagnosticsBusy}
              style={styles.diagnosticsButton}
              onPress={() => {
                setDiagnosticsBusy(true);
                void uploadNow().finally(() => setDiagnosticsBusy(false));
              }}
            >
              <Text style={styles.diagnosticsButtonText}>Upload now</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="time-tracking-refresh-diagnostics"
              accessibilityRole="button"
              disabled={diagnosticsBusy}
              style={styles.diagnosticsButton}
              onPress={() => {
                setDiagnosticsBusy(true);
                void refreshDiagnostics().finally(() =>
                  setDiagnosticsBusy(false),
                );
              }}
            >
              <Text style={styles.diagnosticsButtonText}>Refresh</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : null}
    </PanelModalFrame>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modal: { width: '88%', maxWidth: 420 },
    settingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 16,
      paddingVertical: 10,
    },
    label: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    selector: {
      minWidth: 120,
      maxWidth: '62%',
      flexShrink: 1,
      paddingHorizontal: 12,
      paddingVertical: 9,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    selectorText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      textAlign: 'center',
    },
    pluginInput: {
      minWidth: 120,
      maxWidth: '62%',
      flexShrink: 1,
      paddingHorizontal: 12,
      paddingVertical: 9,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
    fallbackText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      marginBottom: 4,
    },
    diagnosticsToggle: {
      alignSelf: 'flex-end',
      paddingHorizontal: 12,
      paddingVertical: 8,
    },
    diagnosticsToggleText: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    diagnosticsPanel: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
      padding: 12,
      gap: 4,
    },
    diagnosticsText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
    },
    diagnosticsDetail: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
    },
    diagnosticsError: {
      color: theme.danger,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
    },
    diagnosticsTableTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
      marginTop: 8,
    },
    diagnosticsTable: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 6,
      overflow: 'hidden',
    },
    diagnosticsTableRow: {
      flexDirection: 'row',
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    diagnosticsTableHeader: {
      color: theme.textSecondary,
      backgroundColor: theme.surface,
      fontSize: 10,
      fontWeight: '600',
      paddingHorizontal: 4,
      paddingVertical: 5,
    },
    diagnosticsTableCell: {
      color: theme.text,
      fontSize: 10,
      paddingHorizontal: 4,
      paddingVertical: 5,
    },
    diagnosticsStatusColumn: {
      flex: 1.1,
    },
    diagnosticsSessionColumn: {
      flex: 1,
    },
    diagnosticsTimeColumn: {
      flex: 1.45,
    },
    diagnosticsDurationColumn: {
      flex: 0.9,
      textAlign: 'right',
    },
    diagnosticsEmpty: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      padding: 8,
    },
    diagnosticsActions: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 8,
      marginTop: 8,
    },
    diagnosticsButton: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surface,
      paddingHorizontal: 12,
      paddingVertical: 8,
    },
    diagnosticsButtonText: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
    },
  });

export default GlobalSettingsModal;
