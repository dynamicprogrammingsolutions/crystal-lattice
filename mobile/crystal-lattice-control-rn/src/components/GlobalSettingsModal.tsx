import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  MARKDOWN_BASE_FONT_SIZE_OPTIONS,
  MARKDOWN_HEADER_SIZE_OPTIONS,
  useMarkdownDisplayPreferences,
  type MarkdownBaseFontSize,
  type MarkdownHeaderSize,
} from '@crystal-lattice/frontend-rn-components';

import OptionsPickerModal, { type OptionItem } from './OptionsPickerModal';
import PanelModalFrame from './PanelModalFrame';
import { useTheme, type Theme } from '../theme';
import { useHomeWorkspace } from '../HomeWorkspaceContext';
import type { RecentSessionsWindow } from '../homeWorkspaceState';

interface GlobalSettingsModalProps {
  visible: boolean;
  onRequestClose: () => void;
}

const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  visible,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const { preferences, setPreferences } = useMarkdownDisplayPreferences();
  const { recentSessionsWindow, setRecentSessionsWindow } = useHomeWorkspace();
  const [picker, setPicker] = useState<'font' | 'headers' | 'recent' | null>(null);
  const options: OptionItem[] =
    picker === 'font'
      ? MARKDOWN_BASE_FONT_SIZE_OPTIONS.map((option) => ({
          value: String(option.value),
          label: option.label,
        }))
      : picker === 'headers'
        ? MARKDOWN_HEADER_SIZE_OPTIONS.map((option) => ({ ...option }))
        : [
            { value: '24h', label: 'Last 24 hours' },
            { value: '3d', label: 'Last 3 days' },
            { value: '1w', label: 'Last week' },
          ];

  return (
    <PanelModalFrame
      visible={visible}
      title="Settings"
      onRequestClose={onRequestClose}
      contentStyle={styles.modal}
      testID="global-settings-modal"
      overlayChildren={
        <OptionsPickerModal
          visible={visible && picker !== null}
          options={options}
          useModal={false}
          onRequestClose={() => setPicker(null)}
          onSelect={(value) => {
            if (picker === 'recent') {
              setRecentSessionsWindow(value as RecentSessionsWindow);
              setPicker(null);
              return;
            }
            setPreferences(
              picker === 'font'
                ? {
                    ...preferences,
                    baseFontSize: Number(value) as MarkdownBaseFontSize,
                  }
                : {
                    ...preferences,
                    headerSize: value as MarkdownHeaderSize,
                  },
            );
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
  });

export default GlobalSettingsModal;