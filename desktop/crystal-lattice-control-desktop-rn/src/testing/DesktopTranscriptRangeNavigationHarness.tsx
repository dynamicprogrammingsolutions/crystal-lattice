import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type {
  AgentBackend,
  IndexedMessage,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { ApplicationPluginsProvider } from '@crystal-lattice/frontend-sdk-react';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { ChatPane } from '../chat/ChatPane';
import { useDesktopTheme } from '../theme/useDesktopTheme';

const CONNECTION_ID = 'transcript-range-navigation';
const SESSION_ID = 'transcript-range-navigation-session';
const MESSAGE_COUNT = 200;

const RAW_SCROLL_MESSAGE_INDEX = 101;

type TextSurfaceScenario = 'none' | 'raw' | 'code' | 'reasoning' | 'tool';

function normalizeTextSurfaceScenario(value: string): TextSurfaceScenario {
  return value === 'raw' ||
    value === 'code' ||
    value === 'reasoning' ||
    value === 'tool'
    ? value
    : 'none';
}

function buildMessages(textSurfaceScenario: TextSurfaceScenario): IndexedMessage[] {
  return Array.from({ length: MESSAGE_COUNT }, (_, index) => {
    const defaultMessage = {
      role: index % 4 === 0 ? 'user' : 'assistant',
      content: Array.from(
        { length: 2 + (index % 4) },
        (_unused, line) =>
          `Desktop range navigation message ${index}, line ${line + 1}.`,
      ).join('\n'),
    };
    if (index !== RAW_SCROLL_MESSAGE_INDEX) {
      return { index, message: defaultMessage };
    }
    if (textSurfaceScenario === 'raw') {
      return {
        index,
        message: {
          role: 'assistant',
          content: Array.from(
            { length: 90 },
            (_unused, line) =>
              `Desktop raw scroll message ${index}, line ${line + 1}.`,
          ).join('\n'),
        },
      };
    }
    if (textSurfaceScenario === 'code') {
      return {
        index,
        message: {
          role: 'assistant',
          content: [
            '```typescript',
            ...Array.from(
              { length: 90 },
              (_unused, line) => `const codeLine${line + 1} = ${line + 1};`,
            ),
            '```',
          ].join('\n'),
        },
      };
    }
    if (textSurfaceScenario === 'reasoning') {
      return {
        index,
        message: {
          role: 'assistant',
          content: 'Reasoning harness answer.',
          metadata: {
            reasoning: Array.from(
              { length: 80 },
              (_unused, line) =>
                `Desktop reasoning detail ${index}, line ${line + 1}.`,
            ).join('\n'),
          },
        },
      };
    }
    if (textSurfaceScenario === 'tool') {
      return {
        index,
        message: {
          role: 'tool',
          content: Array.from(
            { length: 80 },
            (_unused, line) =>
              `Desktop tool result ${index}, line ${line + 1}.`,
          ).join('\n'),
        },
      };
    }
    return { index, message: defaultMessage };
  });
}

const SESSION_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: 1,
  preview: 'Transcript range navigation',
  metadata: {},
  presentation: {
    title: 'Transcript range navigation',
    subtitle: 'Production desktop chat range harness',
    meta: `${MESSAGE_COUNT} messages`,
  },
};

function normalizeBound(value: number | undefined, fallback: number): number {
  if (value == null) {
    return fallback;
  }
  const relative = value < 0 ? MESSAGE_COUNT + value : value;
  return Math.max(0, Math.min(MESSAGE_COUNT, relative));
}

export function DesktopTranscriptRangeNavigationHarness({
  transcriptTextSurfaceScenario = 'none',
}: {
  transcriptTextSurfaceScenario?: string;
}): React.JSX.Element {
  (globalThis as any).CLC_DEBUG_TRANSCRIPT_RANGE_NAVIGATION = true;
  (globalThis as any).CLC_DEBUG_CHAT_SCROLL_COORDINATOR = true;
  const theme = useDesktopTheme();
  const [loadedRange, setLoadedRange] = useState('loading');
  const textSurfaceScenario = normalizeTextSurfaceScenario(
    transcriptTextSurfaceScenario,
  );
  const allMessages = useMemo(
    () => buildMessages(textSurfaceScenario),
    [textSurfaceScenario],
  );
  const backend = useMemo(
    () =>
      ({
        kind: 'inProcess',
        getCapabilities: () => ({
          featureCompletions: false,
          sessionUiSchema: false,
          sessionConfigOverrides: false,
          sessionPlugins: false,
          applicationActions: false,
          applicationConfig: false,
        }),
        listAgents: async () => ['default'],
        getSessionAgent: async () => 'default',
        listMessages: async (
          _sessionId: string,
          params: { start?: number; end?: number } = {},
        ) => {
          const start = normalizeBound(params.start, 0);
          const end = normalizeBound(params.end, MESSAGE_COUNT);
          const messages = allMessages.slice(start, end);
          setLoadedRange(
            messages.length > 0
              ? `${messages[0].index}:${messages[messages.length - 1].index}`
              : 'empty',
          );
          return {
            messages,
            cursorEventId: 'range-navigation:1',
            activeRequestId: null,
            readonly: false,
            snapshotId: null,
          };
        },
        getSessionSummary: async () => SESSION_SUMMARY,
        getSelectedSessionSnapshot: async () => null,
        clearSelectedSessionSnapshot: async () => {},
        getSessionUiSchema: async () => [],
        getSessionApplicationUiSchema: async () => [],
        getSessionOverrides: async () => ({}),
        getSessionConfigSchema: async () => [],
        getSessionBaseConfig: async () => ({}),
        listApplicationActions: async () => [],
        listApplicationUiSchema: async () => [],
        getLatestEventId: async () => 'range-navigation:1',
        listEvents: async () => ({
          events: [],
          latestEventId: 'range-navigation:1',
          cursorExpired: false,
        }),
      }) as unknown as AgentBackend,
    [allMessages],
  );

  return (
    <ThemeProvider theme={theme}>
      <ApplicationPluginsProvider
        backend={backend}
        connectionId={CONNECTION_ID}
      >
        <View
          style={styles.root}
          testID="transcript-range-navigation-harness-ready"
        >
          <View
            accessible
            accessibilityLabel={`Loaded range ${loadedRange}`}
            testID="transcript-range-navigation-loaded-range"
          >
            <Text>{loadedRange}</Text>
          </View>
          <ChatPane
            isVisible
            isActive
            connectionId={CONNECTION_ID}
            connectionName="Range Navigation"
            sessionId={SESSION_ID}
            sessionSummary={SESSION_SUMMARY}
            title="Transcript range navigation"
            subtitle="Production desktop ChatPane harness"
            backend={backend}
            cachedEntry={{
              connectionId: CONNECTION_ID,
              sessionId: SESSION_ID,
              messages: allMessages.slice(100, 200),
              lastLoadedAt: 1,
              cursorEventId: 'range-navigation:1',
              activeRequestId: null,
              rangeStartText: '100',
              rangeEndText: '200',
            }}
            messagesCacheHydrated
            onUpdateCache={() => {}}
            onOpenSessionTab={() => {}}
          />
        </View>
      </ApplicationPluginsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
});
