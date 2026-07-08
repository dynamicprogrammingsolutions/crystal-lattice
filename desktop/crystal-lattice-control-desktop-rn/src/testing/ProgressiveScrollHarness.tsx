import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ProgressiveScrollList } from '../ui/ProgressiveScrollList';
import { DesktopWindowManager, desktopWindowEvents } from '../windows/desktopWindowManager';

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

type ProgressiveScrollHarnessProps = {
  scrollHarnessRunId?: string;
};

export function ProgressiveScrollHarness({
  scrollHarnessRunId = '',
}: ProgressiveScrollHarnessProps): React.JSX.Element {
  const listRef = useRef<any>(null);
  const lastCommandKeyRef = useRef<string | null>(null);
  const expectedAnchorRef = useRef<any>(null);
  const [status, setStatus] = useState('ready');
  const messages = useMemo(() => buildMessages(), []);

  const recordHarnessState = useCallback((command: string, statusOverride?: string) => {
    const getVisibleAnchor = listRef.current?.getVisibleAnchor;
    const getLastWindowChangeAnchor = listRef.current?.getLastWindowChangeAnchor;
    const getRenderedWindowRange = listRef.current?.getRenderedWindowRange;
    const getItemViewportOffset = listRef.current?.getItemViewportOffset;
    Promise.resolve(typeof getVisibleAnchor === 'function' ? getVisibleAnchor() : null)
      .then((anchor: any) => {
        const windowRange =
          typeof getRenderedWindowRange === 'function' ? getRenderedWindowRange() : null;
        const windowChangeAnchor =
          typeof getLastWindowChangeAnchor === 'function'
            ? getLastWindowChangeAnchor()
            : null;
        return Promise.resolve(
          typeof getItemViewportOffset === 'function'
            ? getItemViewportOffset('msg-120')
            : null,
        ).then((message120Offset) =>
          Promise.resolve(
            typeof getItemViewportOffset === 'function' && windowChangeAnchor?.key
              ? getItemViewportOffset(windowChangeAnchor.key)
              : null,
          ).then((windowChangeAnchorActualOffset) => ({
            message120Offset,
            windowChangeAnchorActualOffset,
          })),
        ).then(({ message120Offset, windowChangeAnchorActualOffset }) => {
          DesktopWindowManager?.recordProgressiveScrollHarnessState?.({
            command,
            runId: scrollHarnessRunId,
            status: statusOverride ?? status,
            anchorKey: anchor?.key ?? null,
            anchorSourceIndex: anchor?.sourceIndex ?? null,
            anchorOffsetFromViewportTop:
              typeof anchor?.offsetFromViewportTop === 'number'
                ? Math.round(anchor.offsetFromViewportTop)
                : null,
            message120OffsetFromViewportTop:
              typeof message120Offset === 'number' ? Math.round(message120Offset) : null,
            expectedAnchorKey: expectedAnchorRef.current?.key ?? null,
            expectedAnchorSourceIndex: expectedAnchorRef.current?.sourceIndex ?? null,
            expectedAnchorOffsetFromViewportTop:
              typeof expectedAnchorRef.current?.offsetFromViewportTop === 'number'
                ? Math.round(expectedAnchorRef.current.offsetFromViewportTop)
                : null,
            windowChangeAnchorKey: windowChangeAnchor?.key ?? null,
            windowChangeAnchorSourceIndex: windowChangeAnchor?.sourceIndex ?? null,
            windowChangeAnchorOffsetFromViewportTop:
              typeof windowChangeAnchor?.offsetFromViewportTop === 'number'
                ? Math.round(windowChangeAnchor.offsetFromViewportTop)
                : null,
            windowChangeAnchorActualOffsetFromViewportTop:
              typeof windowChangeAnchorActualOffset === 'number'
                ? Math.round(windowChangeAnchorActualOffset)
                : null,
            windowStart: windowRange?.start ?? null,
            windowEnd: windowRange?.end ?? null,
            dataLength: windowRange?.length ?? messages.length,
          });
        });
      })
      .catch(() => {
        DesktopWindowManager?.recordProgressiveScrollHarnessState?.({
          command,
          runId: scrollHarnessRunId,
          status: 'state error',
          dataLength: messages.length,
        });
      });
  }, [messages.length, scrollHarnessRunId, status]);

  const recordAfterLayout = useCallback(
    (command: string, statusOverride?: string) => {
      const startedAtMs = Date.now();
      const poll = () => {
        const hasPendingScrollAction = listRef.current?.hasPendingScrollAction;
        const pending =
          typeof hasPendingScrollAction === 'function' && hasPendingScrollAction();
        if (!pending || Date.now() - startedAtMs > 4000) {
          recordHarnessState(command, statusOverride);
          return;
        }
        setTimeout(poll, 100);
      };
      setTimeout(poll, 100);
    },
    [recordHarnessState],
  );

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
        const nextStatus = `anchor ${anchor.key} index ${anchor.sourceIndex} y ${Math.round(
            anchor.offsetFromViewportTop,
          )}`;
        setStatus(nextStatus);
        recordHarnessState('readAnchor', nextStatus);
      })
      .catch(() => setStatus('anchor error'));
  }, [recordHarnessState]);

  const executeHarnessCommand = useCallback(
    (command: string) => {
      if (command === 'top') {
        setStatus('command top');
        listRef.current?.scrollToOffset?.({ offset: 0, animated: false });
        recordAfterLayout(command, 'command top');
      } else if (command === 'bottom') {
        setStatus('command bottom');
        listRef.current?.scrollToEnd?.({ animated: false });
        recordAfterLayout(command, 'command bottom');
      } else if (command === 'message120') {
        setStatus('command message120');
        listRef.current?.scrollToItemAnchor?.({
          key: 'msg-120',
          sourceIndex: 120,
          offsetFromViewportTop: 40,
          beforeCount: 40,
          afterCount: 59,
          animated: false,
        });
        recordAfterLayout(command, 'command message120');
      } else if (command === 'readAnchor') {
        refreshVisibleAnchor();
      } else if (command === 'loadAbove') {
        setStatus('command loadAbove');
        Promise.resolve(listRef.current?.getVisibleAnchor?.()).then((anchor) => {
          expectedAnchorRef.current = anchor;
          listRef.current?.loadMoreTop?.();
          recordAfterLayout(command, 'command loadAbove');
        });
      } else if (command === 'loadBelow') {
        setStatus('command loadBelow');
        Promise.resolve(listRef.current?.getVisibleAnchor?.()).then((anchor) => {
          expectedAnchorRef.current = anchor;
          listRef.current?.loadMoreBottom?.();
          recordAfterLayout(command, 'command loadBelow');
        });
      }
    },
    [recordAfterLayout, refreshVisibleAnchor],
  );

  useEffect(() => {
    const subscription = desktopWindowEvents?.addListener(
      'progressiveScrollHarnessCommand',
      (event: { command?: string; postedAtMs?: unknown; runId?: unknown }) => {
        const command = event?.command;
        if (typeof command !== 'string') {
          return;
        }
        if (typeof event?.runId === 'string' && event.runId !== scrollHarnessRunId) {
          return;
        }
        lastCommandKeyRef.current = `${command}:${String(event?.postedAtMs ?? '')}`;
        executeHarnessCommand(command);
      },
    );
    const interval = setInterval(() => {
      DesktopWindowManager?.readProgressiveScrollHarnessCommand?.()
        .then((payload) => {
          const command = payload?.command;
          const postedAtMs = payload?.postedAtMs;
          if (typeof command !== 'string') {
            return;
          }
          if (
            typeof payload?.runId === 'string' &&
            payload.runId !== scrollHarnessRunId
          ) {
            return;
          }
          const commandKey = `${command}:${String(postedAtMs ?? '')}`;
          if (lastCommandKeyRef.current === commandKey) {
            return;
          }
          lastCommandKeyRef.current = commandKey;
          executeHarnessCommand(command);
        })
        .catch(() => {});
    }, 250);
    return () => {
      subscription?.remove();
      clearInterval(interval);
    };
  }, [executeHarnessCommand, recordAfterLayout, scrollHarnessRunId]);

  return (
    <View
      testID="scroll-harness-root"
      accessible={false}
      accessibilityLabel="Progressive Scroll Harness Root"
      style={styles.root}
    >
      <View style={styles.toolbar}>
        <Text
          testID="scroll-harness-title"
          accessibilityLabel="Progressive Scroll Harness"
          style={styles.title}
        >
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

      <Text
        testID="scroll-harness-status"
        accessibilityLabel={`Harness status ${status}`}
        style={styles.status}
      >
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
          <View
            testID={`scroll-harness-message-${item.index}`}
            accessible
            accessibilityLabel={`Message ${item.index}`}
            style={styles.row}
          >
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