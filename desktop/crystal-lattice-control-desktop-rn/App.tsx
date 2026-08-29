import * as React from 'react';
import { StyleSheet, View } from 'react-native';

import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  ThemeProvider,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  type MarkdownBaseFontSize,
  type MarkdownHeaderSize,
} from '@crystal-lattice/frontend-rn-components';

import { DesktopRoot } from './src/DesktopRoot';
import { ProgressiveScrollHarness } from './src/testing/ProgressiveScrollHarness';
import { DesktopMarkdownGeometryHarness } from './src/testing/DesktopMarkdownGeometryHarness';
import { useDesktopTheme } from './src/theme/useDesktopTheme';
import {
  DEFAULT_TAB_STRIP_STYLE,
  parseTabStripStyle,
  type TabStripStyle,
} from './src/tabs/tabStripStyle';

export interface AppProps {
  initialTabStripStyle?: TabStripStyle;
  initialSessionsFollowActiveTabEnabled?: boolean;
  initialMarkdownBaseFontSize?: MarkdownBaseFontSize;
  initialMarkdownHeaderSize?: MarkdownHeaderSize;
  enableScrollTestHarness?: boolean;
  enableMarkdownGeometryHarness?: boolean;
}

export default function App(props: AppProps) {
  const theme = useDesktopTheme();
  const initialTabStripStyle =
    parseTabStripStyle((props as any)?.initialTabStripStyle) ?? DEFAULT_TAB_STRIP_STYLE;

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root}>
        {(props as any)?.enableMarkdownGeometryHarness === true ? (
          <DesktopMarkdownGeometryHarness
            initialMarkdownBaseFontSize={(props as any)?.initialMarkdownBaseFontSize}
            initialMarkdownHeaderSize={(props as any)?.initialMarkdownHeaderSize}
          />
        ) : (props as any)?.enableScrollTestHarness === true ? (
          <ProgressiveScrollHarness />
        ) : (
          <DesktopRoot
            initialTabStripStyle={initialTabStripStyle}
            initialSessionsFollowActiveTabEnabled={
              typeof (props as any)?.initialSessionsFollowActiveTabEnabled === 'boolean'
                ? (props as any).initialSessionsFollowActiveTabEnabled
                : undefined
            }
            initialMarkdownBaseFontSize={normalizeMarkdownBaseFontSize(
              (props as any)?.initialMarkdownBaseFontSize ??
                DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
            )}
            initialMarkdownHeaderSize={normalizeMarkdownHeaderSize(
              (props as any)?.initialMarkdownHeaderSize ??
                DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.headerSize,
            )}
          />
        )}
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
