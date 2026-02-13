import * as React from 'react';
import { StyleSheet, View } from 'react-native';

import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { DesktopRoot } from './src/DesktopRoot';
import { useDesktopTheme } from './src/theme/useDesktopTheme';
import {
  DEFAULT_TAB_STRIP_STYLE,
  parseTabStripStyle,
  type TabStripStyle,
} from './src/tabs/tabStripStyle';

export interface AppProps {
  initialTabStripStyle?: TabStripStyle;
  initialSessionsFollowActiveTabEnabled?: boolean;
}

export default function App(props: AppProps) {
  const theme = useDesktopTheme();
  const initialTabStripStyle =
    parseTabStripStyle((props as any)?.initialTabStripStyle) ?? DEFAULT_TAB_STRIP_STYLE;

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root}>
        <DesktopRoot
          initialTabStripStyle={initialTabStripStyle}
          initialSessionsFollowActiveTabEnabled={
            typeof (props as any)?.initialSessionsFollowActiveTabEnabled === 'boolean'
              ? (props as any).initialSessionsFollowActiveTabEnabled
              : undefined
          }
        />
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
