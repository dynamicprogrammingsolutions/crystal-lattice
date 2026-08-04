import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import MarkdownMessageContent from '../components/MarkdownMessageContent';
import SelectableMarkdownMessageContent from '../components/SelectableMarkdownMessageContent';
import { ThemeProvider, lightTheme } from '../theme';

export const ORDERED_LIST_REPRO_MARKDOWN = [
  '3. First ordered item should be numbered three.',
  '',
  '   Continuation paragraph must not repeat the number.',
  '',
  '4. Second ordered item should be numbered four.',
].join('\n');

export function MobileOrderedListMarkdownHarness(): React.JSX.Element {
  return (
    <ThemeProvider theme={lightTheme}>
      <View style={styles.root} testID="ordered-list-markdown-harness-ready">
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.title}>Ordered List Markdown Repro</Text>
          <Text style={styles.label}>Enriched markdown</Text>
          <View testID="ordered-list-enriched-renderer">
            <SelectableMarkdownMessageContent text={ORDERED_LIST_REPRO_MARKDOWN} />
          </View>
          <Text style={styles.label}>Legacy markdown</Text>
          <View testID="ordered-list-legacy-renderer">
            <MarkdownMessageContent text={ORDERED_LIST_REPRO_MARKDOWN} />
          </View>
        </ScrollView>
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: '#FFFFFF',
    flex: 1,
  },
  content: {
    paddingHorizontal: 32,
    paddingTop: 32,
  },
  title: {
    color: '#000000',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 20,
  },
  label: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 12,
  },
});