import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import SelectableCodeBlock from '../components/SelectableCodeBlock';
import { ThemeProvider, lightTheme } from '../theme';

const REPRO_LINES = [
  'const aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = "first long line";',
  'const bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb = "second long line";',
  'const cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc = "third long line";',
  'const dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd = "fourth long line";',
  'const eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee = "fifth long line";',
];

export function MobileSelectableCodeBlockHarness(): React.JSX.Element {
  const [screen, setScreen] = useState<'messages' | 'sessions'>('messages');

  return (
    <ThemeProvider theme={lightTheme}>
      <View style={styles.root} testID="code-block-harness-ready">
        <View style={styles.tabs}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setScreen('sessions')}
            style={[styles.tab, screen === 'sessions' && styles.activeTab]}
            testID="code-block-harness-sessions-tab"
          >
            <Text style={styles.tabText}>Sessions</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => setScreen('messages')}
            style={[styles.tab, screen === 'messages' && styles.activeTab]}
            testID="code-block-harness-messages-tab"
          >
            <Text style={styles.tabText}>Messages</Text>
          </Pressable>
        </View>

        {screen === 'messages' ? (
          <ScrollView
            contentContainerStyle={styles.content}
            testID="code-block-harness-scroll"
          >
            <Text style={styles.title}>Selectable Code Block Repro</Text>
            {REPRO_LINES.map((code, index) => (
              <SelectableCodeBlock
                code={`${code}\n`}
                key={code}
                language="ts"
                testID={`code-block-repro-${index}`}
              />
            ))}
          </ScrollView>
        ) : (
          <View style={styles.placeholder} testID="code-block-harness-placeholder">
            <Text style={styles.title}>Sessions Placeholder</Text>
          </View>
        )}
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: '#F2F2F7',
    flex: 1,
  },
  tabs: {
    backgroundColor: '#FFFFFF',
    borderBottomColor: '#D1D1D6',
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 10,
  },
  tab: {
    borderColor: '#D1D1D6',
    borderRadius: 6,
    borderWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  activeTab: {
    backgroundColor: '#DCEBFF',
    borderColor: '#0A84FF',
  },
  tabText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    padding: 16,
  },
  title: {
    color: '#000000',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  placeholder: {
    flex: 1,
    padding: 16,
  },
});