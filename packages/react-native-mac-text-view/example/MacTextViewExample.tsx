import React, { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { MacTextView, type MacTextViewHandle } from '../src';

export function MacTextViewExample(): React.JSX.Element {
  const [value, setValue] = useState('');
  const [height, setHeight] = useState(34);
  const ref = useRef<MacTextViewHandle | null>(null);

  return (
    <View style={styles.root}>
      <Text style={styles.title}>MacTextView Example</Text>
      <MacTextView
        ref={ref}
        style={styles.input}
        placeholder="Type here..."
        initialText=""
        autoGrow
        minHeight={34}
        maxHeight={160}
        onChangeText={setValue}
        onHeightChange={setHeight}
        onSubmit={() => {
          // Example only.
        }}
      />
      <Text style={styles.meta}>Text length: {value.length}</Text>
      <Text style={styles.meta}>Resolved height: {height}</Text>
      <View style={styles.row}>
        <Pressable style={styles.button} onPress={() => ref.current?.focus()}>
          <Text style={styles.buttonText}>Focus</Text>
        </Pressable>
        <Pressable
          style={styles.button}
          onPress={() => ref.current?.setText('Programmatically inserted text')}
        >
          <Text style={styles.buttonText}>Set Text</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    gap: 12,
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
  },
  input: {
    minHeight: 34,
    borderWidth: 1,
    borderColor: '#c9c9c9',
    borderRadius: 10,
    paddingHorizontal: 0,
  },
  meta: {
    fontSize: 12,
    color: '#666666',
  },
  row: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    borderWidth: 1,
    borderColor: '#c9c9c9',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  buttonText: {
    fontSize: 12,
    fontWeight: '600',
  },
});