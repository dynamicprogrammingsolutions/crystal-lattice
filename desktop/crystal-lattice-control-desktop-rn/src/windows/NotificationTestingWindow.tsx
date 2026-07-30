import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';
import {
  NotificationBanner,
  type NotificationVariant,
} from '../ui/NotificationBanner';

interface ActiveBanner {
  id: number;
  variant: NotificationVariant;
  title: string;
  message: string;
}

const VARIANT_DEFS: Array<{
  variant: NotificationVariant;
  label: string;
  title: string;
  message: string;
}> = [
  { variant: 'info', label: 'Show Info', title: 'Info', message: 'This is an informational notification banner.' },
  { variant: 'success', label: 'Show Success', title: 'Success', message: 'The operation completed successfully.' },
  { variant: 'warning', label: 'Show Warning', title: 'Warning', message: 'Something needs your attention.' },
  { variant: 'error', label: 'Show Error', title: 'Error', message: 'The operation failed. Please try again.' },
];

export function NotificationTestingWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <NotificationTestingWindowInner />
    </ThemeProvider>
  );
}

function NotificationTestingWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [banners, setBanners] = useState<ActiveBanner[]>([]);
  const [nextId, setNextId] = useState(1);

  const closeWindow = useCallback(() => {
    DesktopWindowManager?.closeReactWindow({ windowKey: 'notificationTesting' });
  }, []);

  const showBanner = useCallback((variant: NotificationVariant, title: string, message: string) => {
    const id = nextId;
    setNextId((prev) => prev + 1);
    setBanners((prev) => [...prev, { id, variant, title, message }]);
  }, [nextId]);

  const dismissBanner = useCallback((id: number) => {
    setBanners((prev) => prev.filter((b) => b.id !== id));
  }, []);

  return (
    <View style={styles.root}>
      <View style={styles.headerRow}>
        <View style={styles.header}>
          <Text style={styles.title}>Notification Testing</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            Preview notification banner colors for each variant.
          </Text>
        </View>

        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            return [
              styles.closeButton,
              (hovered || state.pressed) && styles.closeButtonHovered,
            ];
          }}
          onPress={closeWindow}
        >
          <Text style={styles.closeButtonText}>Close</Text>
        </Pressable>
      </View>

      <View style={styles.listContainer}>
        <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
          <View style={styles.actionsRow}>
            {VARIANT_DEFS.map((def) => (
              <Pressable
                key={def.variant}
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.actionButton,
                    (hovered || state.pressed) && styles.actionButtonPressed,
                  ];
                }}
                onPress={() => {
                  showBanner(def.variant, def.title, def.message);
                }}
              >
                <Text style={styles.actionButtonText}>{def.label}</Text>
              </Pressable>
            ))}
          </View>

          <View style={styles.bannersContainer}>
            {banners.length === 0 ? (
              <Text style={styles.helperText}>
                Press a button above to show a notification banner.
              </Text>
            ) : (
              banners.map((banner) => (
                <NotificationBanner
                  key={banner.id}
                  variant={banner.variant}
                  title={banner.title}
                  message={banner.message}
                  onDismiss={() => {
                    dismissBanner(banner.id);
                  }}
                />
              ))
            )}
          </View>
        </ScrollView>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.background,
      padding: 16,
      gap: 12,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12,
    },
    header: {
      gap: 4,
      flex: 1,
    },
    closeButton: {
      borderWidth,
      borderColor: theme.primary,
      backgroundColor: theme.primary,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 7,
      alignItems: 'center',
      justifyContent: 'center',
    },
    closeButtonHovered: {
      opacity: 0.92,
    },
    closeButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    title: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    listContainer: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    list: {
      flex: 1,
    },
    listContent: {
      padding: 12,
      gap: 12,
    },
    actionsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    actionButton: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      backgroundColor: theme.surfaceAlt,
      borderWidth,
      borderColor: theme.border,
      minWidth: 110,
      alignItems: 'center',
      justifyContent: 'center',
    },
    actionButtonPressed: {
      opacity: 0.85,
    },
    actionButtonText: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.text,
    },
    bannersContainer: {
      gap: 10,
    },
    helperText: {
      fontSize: 12,
      color: theme.textSecondary,
      paddingVertical: 8,
    },
  });
}