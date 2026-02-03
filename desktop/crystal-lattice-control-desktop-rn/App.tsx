import * as React from 'react';
import { StyleSheet, View } from 'react-native';

import {
  ThemeProvider,
  useSystemTheme,
} from '@crystal-lattice/frontend-rn-components';

import { DesktopRoot } from './src/DesktopRoot';

export default function App() {
  const theme = useSystemTheme();

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root}>
        <DesktopRoot />
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
