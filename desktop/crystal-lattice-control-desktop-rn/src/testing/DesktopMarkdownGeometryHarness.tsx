import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  MarkdownDisplayPreferencesProvider,
  ThemeProvider,
  applyDisplayTypographyPreset,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  useTheme,
  type MarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';

import MarkdownMessageContent from '../chat/MarkdownMessageContent';
import {
  DesktopWindowManager,
  desktopWindowEvents,
} from '../windows/desktopWindowManager';

interface DesktopMarkdownGeometryHarnessProps {
  initialMarkdownBaseFontSize?: unknown;
  initialMarkdownHeaderSize?: unknown;
}

export function DesktopMarkdownGeometryHarness({
  initialMarkdownBaseFontSize,
  initialMarkdownHeaderSize,
}: DesktopMarkdownGeometryHarnessProps): React.JSX.Element {
  const baseTheme = useTheme();
  const [preferences, setPreferences] = useState<MarkdownDisplayPreferences>({
    baseFontSize: normalizeMarkdownBaseFontSize(initialMarkdownBaseFontSize),
    headerSize: normalizeMarkdownHeaderSize(initialMarkdownHeaderSize),
    markdownRenderer: 'react-native-markdown-display',
    codeBlockRenderer: 'syntax-highlighter',
  });
  const [geometry, setGeometry] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!desktopWindowEvents) return;
    const fontSub = desktopWindowEvents.addListener(
      'markdownBaseFontSizeChanged',
      (payload: any) => {
        setPreferences((current) => ({
          ...current,
          baseFontSize: normalizeMarkdownBaseFontSize(payload?.baseFontSize),
        }));
      },
    );
    const headerSub = desktopWindowEvents.addListener(
      'markdownHeaderSizeChanged',
      (payload: any) => {
        setPreferences((current) => ({
          ...current,
          headerSize: normalizeMarkdownHeaderSize(payload?.headerSize),
        }));
      },
    );
    return () => {
      fontSub.remove();
      headerSub.remove();
    };
  }, []);

  const valueLabel = useMemo(
    () => `${preferences.baseFontSize}:${preferences.headerSize}`,
    [preferences],
  );
  const theme = useMemo(
    () => applyDisplayTypographyPreset(baseTheme, preferences.baseFontSize),
    [baseTheme, preferences.baseFontSize],
  );

  useEffect(() => {
    if (
      typeof geometry.h1Height !== 'number' ||
      typeof geometry.h6Height !== 'number' ||
      typeof geometry.bodyHeight !== 'number' ||
      typeof geometry.footerHeight !== 'number'
    ) {
      return;
    }
    DesktopWindowManager?.recordMarkdownGeometryHarnessState?.({
      baseFontSize: preferences.baseFontSize,
      headerSize: preferences.headerSize,
      ...geometry,
    });
  }, [geometry, preferences]);

  const recordHeight = (key: string, height: number) => {
    setGeometry((current) =>
      current[key] === height ? current : { ...current, [key]: height },
    );
  };

  return (
    <MarkdownDisplayPreferencesProvider value={preferences}>
    <ThemeProvider theme={theme}>
    <View style={[styles.root, { backgroundColor: theme.background }]}>
      <Text testID="desktop-markdown-preference-value">{valueLabel}</Text>
      <View
        testID="desktop-markdown-h1"
        onLayout={(event) => recordHeight('h1Height', event.nativeEvent.layout.height)}
      >
        <MarkdownMessageContent text="# Heading one" />
      </View>
      <View
        testID="desktop-markdown-h6"
        onLayout={(event) => recordHeight('h6Height', event.nativeEvent.layout.height)}
      >
        <MarkdownMessageContent text="###### Heading six" />
      </View>
      <View
        testID="desktop-markdown-body"
        onLayout={(event) => recordHeight('bodyHeight', event.nativeEvent.layout.height)}
      >
        <MarkdownMessageContent text="Representative body text." />
      </View>
      <Text
        testID="desktop-message-footer"
        style={{
          fontSize: theme.typography.fontSize.tiny,
          lineHeight: theme.typography.lineHeight.tiny,
        }}
        onLayout={(event) => recordHeight('footerHeight', event.nativeEvent.layout.height)}
      >
        Representative message footer
      </Text>
    </View>
    </ThemeProvider>
    </MarkdownDisplayPreferencesProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    padding: 32,
  },
});