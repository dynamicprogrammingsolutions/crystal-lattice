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
  const [picker, setPicker] = useState<'font' | 'headers' | null>(null);
  const options: OptionItem[] =
    picker === 'font'
      ? MARKDOWN_BASE_FONT_SIZE_OPTIONS.map((option) => ({
          value: String(option.value),
          label: option.label,
        }))
      : MARKDOWN_HEADER_SIZE_OPTIONS.map((option) => ({ ...option }));

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