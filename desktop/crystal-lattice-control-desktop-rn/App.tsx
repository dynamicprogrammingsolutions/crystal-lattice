import * as React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { parseOptionalInt } from '@crystal-lattice/frontend-sdk';
import { buildActionsMenuModel } from '@crystal-lattice/frontend-rn-components';

const demoActionsModel = buildActionsMenuModel({
  baseActions: [
    { key: 'connect', label: 'Connect' },
    { key: 'disconnect', label: 'Disconnect' },
  ],
  pinned: [],
});

export default function App() {
  const parsed = parseOptionalInt('123') ?? '(missing)';

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Crystal Lattice Control (Desktop)</Text>
      <Text style={styles.subtitle}>RN macOS scaffold is wired.</Text>

      <View style={styles.block}>
        <Text style={styles.label}>SDK sanity check:</Text>
        <Text style={styles.value}>parseOptionalInt('123') = {parsed}</Text>
      </View>

      <View style={styles.block}>
        <Text style={styles.label}>Shared components sanity check:</Text>
        <Text style={styles.value}>
          Actions: {demoActionsModel.orderedActions.map((a) => a.key).join(', ')}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
  },
  subtitle: {
    fontSize: 14,
    opacity: 0.7,
  },
  block: {
    paddingTop: 8,
  },
  label: {
    fontSize: 12,
    opacity: 0.7,
  },
  value: {
    fontSize: 14,
  },
});
