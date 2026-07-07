import React, { useCallback, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ProgressiveScrollList } from '../ui/ProgressiveScrollList';

type HarnessMessage = {
  index: number;
  title: string;
  detail: string;
};

const TOTAL_MESSAGES = 220;

function buildMessages(): HarnessMessage[] {
  return Array.from({ length: TOTAL_MESSAGES }, (_, index) => {
    const lines = 1 + (index % 7);
    return {
      index,
      title: `Message ${index}`,
      detail: Array.from({ length: lines }, () => `Variable row content for message ${index}.`).join(
        ' ',
      ),
    };
  });
}

export function ProgressiveScrollHarness(): React.JSX.Element {
  const listRef = useRef<any>(null);
  const [status, setStatus] = useState('ready');
  const messages = useMemo(() => buildMessages(), []);

  const refreshVisibleAnchor = useCallback(() => {
    const getVisibleAnchor = listRef.current?.getVisibleAnchor;
    if (typeof getVisibleAnchor !== 'function') {
      setStatus('anchor unavailable');
      return;
    }
    getVisibleAnchor()
      .then((anchor: any) => {
        if (!anchor) {
          setStatus('anchor none');
          return;
        }
        setStatus(
          `anchor ${anchor.key} index ${anchor.sourceIndex} y ${Math.round(
            anchor.offsetFromViewportTop,
          )}`,
        );
      })
      .catch(() => setStatus('anchor error'));
  }, []);

  return (
    <View testID="scroll-harness-root" style={styles.root}>
      <View style={styles.toolbar}>
        <Text testID="scroll-harness-title" style={styles.title}>
          Progressive Scroll Harness
        </Text>
        <Pressable
          testID="scroll-harness-top"
          accessibilityRole="button"
          accessibilityLabel="Harness scroll to top"
          style={styles.button}
          onPress={() => listRef.current?.scrollToOffset?.({ offset: 0, animated: false })}
        >
          <Text style={styles.buttonText}>Top</Text>
        </Pressable>
        <Pressable
          testID="scroll-harness-bottom"
          accessibilityRole="button"
          accessibilityLabel="Harness scroll to bottom"
          style={styles.button}
          onPress={() => listRef.current?.scrollToEnd?.({ animated: false })}
        >
          <Text style={styles.buttonText}>Bottom</Text>
        </Pressable>
        <Pressable
          testID="scroll-harness-anchor-120"
          accessibilityRole="button"
          accessibilityLabel="Harness scroll to message 120"
          style={styles.button}
          onPress={() =>
            listRef.current?.scrollToItemAnchor?.({
              key: 'msg-120',
              sourceIndex: 120,
              offsetFromViewportTop: 40,
              beforeCount: 40,
              afterCount: 59,
              animated: false,
            })
          }
        >
          <Text style={styles.buttonText}>Msg 120</Text>
        </Pressable>
        <Pressable
          testID="scroll-harness-read-anchor"
          accessibilityRole="button"
          accessibilityLabel="Harness read visible anchor"
          style={styles.button}
          onPress={refreshVisibleAnchor}
        >
          <Text style={styles.buttonText}>Anchor</Text>
        </Pressable>
      </View>

      <Text testID="scroll-harness-status" style={styles.status}>
        {status}
      </Text>

      <ProgressiveScrollList
        testID="scroll-harness-list"
        listRef={listRef}
        style={styles.list}
        contentContainerStyle={styles.listContent}
        data={messages}
        keyExtractor={(item) => `msg-${item.index}`}
        initialWindowSize={50}
        pageSize={50}
        maxWindowSize={100}
        prebuildRows
        defaultAnchorBeforeCount={40}
        defaultAnchorAfterCount={59}
        autoLoadEdges={false}
        scrollEventThrottle={16}
        renderItem={({ item }) => (
          <View testID={`scroll-harness-message-${item.index}`} style={styles.row}>
            <Text style={styles.rowTitle}>{item.title}</Text>
            <Text style={styles.rowDetail}>{item.detail}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  toolbar: {
    minHeight: 48,
    paddingHorizontal: 12,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#D9D9D9',
  },
  title: {
    flex: 1,
    fontSize: 15,
    fontWeight: '700',
    color: '#1F1F1F',
  },
  button: {
    minHeight: 30,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#C8C8C8',
    justifyContent: 'center',
    backgroundColor: '#F5F5F5',
  },
  buttonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#333333',
  },
  status: {
    minHeight: 24,
    paddingHorizontal: 12,
    paddingVertical: 4,
    fontSize: 12,
    color: '#555555',
    borderBottomWidth: 1,
    borderBottomColor: '#ECECEC',
  },
  list: {
    flex: 1,
  },
  listContent: {
    padding: 12,
    gap: 8,
  },
  row: {
    borderWidth: 1,
    borderColor: '#D1D1D1',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#FAFAFA',
  },
  rowTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#222222',
  },
  rowDetail: {
    marginTop: 4,
    fontSize: 12,
    lineHeight: 17,
    color: '#666666',
  },
});