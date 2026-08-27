import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import CenteredModalSurface from './CenteredModalSurface';
import { useTheme, type Theme } from '../theme';

export type PanelModalStatusTone = 'idle' | 'busy' | 'success' | 'error';

export interface PanelModalFrameProps {
  visible: boolean;
  testID?: string;
  title: string;
  titleTestID?: string;
  subtitle?: string;
  onRequestClose: () => void;
  children: React.ReactNode;
  overlayChildren?: React.ReactNode;
  statusText?: string | null;
  statusTone?: PanelModalStatusTone;
  showSpinner?: boolean;
  scroll?: boolean;
  scrollTestID?: string;
  contentStyle?: StyleProp<ViewStyle>;
  bodyStyle?: StyleProp<ViewStyle>;
  scrollContentStyle?: StyleProp<ViewStyle>;
}

const PanelModalFrame: React.FC<PanelModalFrameProps> = ({
  visible,
  testID,
  title,
  titleTestID,
  subtitle,
  onRequestClose,
  children,
  overlayChildren,
  statusText,
  statusTone = 'idle',
  showSpinner = false,
  scroll = false,
  scrollTestID,
  contentStyle,
  bodyStyle,
  scrollContentStyle,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <CenteredModalSurface
      visible={visible}
      testID={testID}
      onRequestClose={onRequestClose}
      overlayChildren={overlayChildren}
      contentStyle={contentStyle}
    >
      <View style={styles.headerRow}>
        <Text testID={titleTestID} style={styles.titleText}>
          {title}
        </Text>
        <TouchableOpacity style={styles.closeButton} onPress={onRequestClose}>
          <Text style={styles.closeButtonText}>Close</Text>
        </TouchableOpacity>
      </View>
      {subtitle ? <Text style={styles.subtitleText}>{subtitle}</Text> : null}
      {(showSpinner || statusText) ? (
        <View style={styles.statusLine}>
          {showSpinner ? <ActivityIndicator size="small" color={theme.primary} /> : null}
          {statusText ? (
            <Text
              style={[
                styles.statusText,
                statusTone === 'error'
                  ? styles.statusTextError
                  : statusTone === 'success'
                    ? styles.statusTextSuccess
                    : null,
              ]}
              numberOfLines={1}
            >
              {statusText}
            </Text>
          ) : null}
        </View>
      ) : null}
      <View style={[styles.body, bodyStyle]}>
        {scroll ? (
          <ScrollView
            testID={scrollTestID}
            style={styles.scroll}
            contentContainerStyle={[styles.scrollContent, scrollContentStyle]}
            keyboardShouldPersistTaps="handled"
          >
            {children}
          </ScrollView>
        ) : (
          children
        )}
      </View>
    </CenteredModalSurface>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    titleText: {
      flex: 1,
      color: theme.text,
      fontSize: theme.typography.fontSize.title,
      fontWeight: '600',
      marginRight: 12,
    },
    closeButton: {
      paddingHorizontal: 8,
      paddingVertical: 6,
    },
    closeButtonText: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    subtitleText: {
      paddingHorizontal: 16,
      paddingTop: 8,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
    },
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      minHeight: 22,
      paddingHorizontal: 16,
      paddingTop: 8,
    },
    statusText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      flexShrink: 1,
    },
    statusTextError: {
      color: theme.danger,
      fontWeight: '600',
    },
    statusTextSuccess: {
      color: theme.success,
      fontWeight: '600',
    },
    body: {
      flexGrow: 0,
      flexShrink: 1,
      paddingHorizontal: 16,
      paddingVertical: 8,
    },
    scroll: {
      flexGrow: 0,
      flexShrink: 1,
    },
    scrollContent: {
      paddingBottom: 8,
    },
  });

export default PanelModalFrame;