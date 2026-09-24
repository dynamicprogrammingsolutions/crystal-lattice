import React, { useMemo, useState } from 'react';
import { StyleSheet, Switch, Text, TextInput, TouchableOpacity, View } from 'react-native';
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
import { useTheme, type Theme } from '../theme';
import { useHomeWorkspace } from '../HomeWorkspaceContext';
import {
  DEFAULT_TIME_TRACKING_PLUGIN_ID,
  type RecentSessionsWindow,
} from '../homeWorkspaceState';
import { resolveMobileMarkdownRendererPreferences } from '../markdownRendererPreferences';

interface GlobalSettingsModalProps {
  visible: boolean;
  onRequestClose: () => void;
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

function optionItems(
  picker: SettingsPicker | null,
): readonly OptionItem[] {
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

const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  visible,
  onRequestClose,
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
  const [picker, setPicker] = useState<SettingsPicker | null>(null);
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
        <View style={styles.settingRow}>
          <Text style={styles.label}>Base font size</Text>
          <TouchableOpacity
            testID="global-settings-base-font-size"
            accessibilityLabel="Base font size"
            style={styles.selector}
            onPress={() => setPicker('font')}
          >
            <Text testID="global-settings-base-font-size-value" style={styles.selectorText}>
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
            <Text testID="global-settings-markdown-headers-value" style={styles.selectorText}>
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
  });

export default GlobalSettingsModal;
