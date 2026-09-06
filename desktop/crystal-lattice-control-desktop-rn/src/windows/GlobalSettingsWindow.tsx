import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

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

const RECENT_OPTIONS = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '3d', label: 'Last 3 days' },
  { value: '1w', label: 'Last week' },
];

const DOUBLE_CLICK_OPTIONS = [
  { value: 'preview', label: 'Preview session' },
  { value: 'open', label: 'Open permanent tab' },
];

type DesktopGlobalSettingKey =
  | 'baseFontSize'
  | 'headerSize'
  | 'recentSessionsWindow'
  | 'sessionDoubleClickAction';

export function applyDesktopGlobalSettingChange(
  current: DesktopGlobalSettings,
  key: DesktopGlobalSettingKey,
  value: string | number,
  write: (params: {
    key: DesktopGlobalSettingKey;
    value: string | number;
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
    ];
    return () => {
      cancelled = true;
      subscriptions.forEach(subscription => subscription.remove());
    };
  }, []);

  const update = useCallback(
    (key: DesktopGlobalSettingKey, value: string | number) => {
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
      </View>
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
  });
}
