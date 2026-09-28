import * as React from 'react';
import { StyleSheet, View } from 'react-native';

import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  ThemeProvider,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  type MarkdownBaseFontSize,
  type MarkdownHeaderSize,
  type RecentSessionsWindow,
} from '@crystal-lattice/frontend-rn-components';

import {
  DesktopRoot,
  type DesktopHumanTimeNativeFixture,
} from './src/DesktopRoot';
import { ProgressiveScrollHarness } from './src/testing/ProgressiveScrollHarness';
import { DesktopMarkdownGeometryHarness } from './src/testing/DesktopMarkdownGeometryHarness';
import { useDesktopTheme } from './src/theme/useDesktopTheme';
import {
  DEFAULT_TAB_STRIP_STYLE,
  parseTabStripStyle,
  type TabStripStyle,
} from './src/tabs/tabStripStyle';
import type { SessionOpenMode } from './src/settings/desktopGlobalSettings';

export interface AppProps {
  initialTabStripStyle?: TabStripStyle;
  initialSessionsFollowActiveTabEnabled?: boolean;
  initialSwitchConnectionWithActiveTabEnabled?: boolean;
  initialMarkdownBaseFontSize?: MarkdownBaseFontSize;
  initialMarkdownHeaderSize?: MarkdownHeaderSize;
  initialRecentSessionsWindow?: RecentSessionsWindow;
  initialSessionDoubleClickAction?: SessionOpenMode;
  enableScrollTestHarness?: boolean;
  enableMarkdownGeometryHarness?: boolean;
  humanTimeNativeFixture?: DesktopHumanTimeNativeFixture;
}

export default function App(props: AppProps) {
  const theme = useDesktopTheme();
  const initialTabStripStyle =
    parseTabStripStyle((props as any)?.initialTabStripStyle) ??
    DEFAULT_TAB_STRIP_STYLE;

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root}>
        {(props as any)?.enableMarkdownGeometryHarness === true ? (
          <DesktopMarkdownGeometryHarness
            initialMarkdownBaseFontSize={
              (props as any)?.initialMarkdownBaseFontSize
            }
            initialMarkdownHeaderSize={
              (props as any)?.initialMarkdownHeaderSize
            }
          />
        ) : (props as any)?.enableScrollTestHarness === true ? (
          <ProgressiveScrollHarness />
        ) : (
          <DesktopRoot
            initialTabStripStyle={initialTabStripStyle}
            initialSessionsFollowActiveTabEnabled={
              typeof (props as any)?.initialSessionsFollowActiveTabEnabled ===
              'boolean'
                ? (props as any).initialSessionsFollowActiveTabEnabled
                : undefined
            }
            initialSwitchConnectionWithActiveTabEnabled={
              typeof (props as any)
                ?.initialSwitchConnectionWithActiveTabEnabled === 'boolean'
                ? (props as any).initialSwitchConnectionWithActiveTabEnabled
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
            initialRecentSessionsWindow={
              (props as any)?.initialRecentSessionsWindow
            }
            initialSessionDoubleClickAction={
              (props as any)?.initialSessionDoubleClickAction
            }
            humanTimeNativeFixture={
              (props as any)?.humanTimeNativeFixture as
                | DesktopHumanTimeNativeFixture
                | undefined
            }
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
