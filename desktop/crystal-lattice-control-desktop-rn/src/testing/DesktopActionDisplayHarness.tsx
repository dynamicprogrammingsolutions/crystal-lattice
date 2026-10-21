import React, { useEffect, useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopGlobalDisplayLayer } from '../ui/DesktopGlobalDisplayLayer';

const LONG_BODY = Array.from(
  { length: 300 },
  (_, index) => `Instruction line ${index}: verify the compiled prompt window.`,
).join('\n');

function createBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

function presentLongActionDisplay(backend: AgentBackend): void {
  emitDisplayPresentation(
    backend,
    normalizeDisplayEnvelope({
      id: 'compiled-system-message',
      source: 'action_response',
      ownershipScope: 'session',
      connectionId: 'local',
      sessionId: 'long-prompt-session',
      display: {
        format: 'text',
        title: 'Compiled system message',
        body: LONG_BODY,
        presentation: 'modal',
        dismissible: true,
        form: {
          kind: 'form',
          inputs: [
            {
              name: 'prompt',
              type: 'multiline',
              label: 'Prompt',
              default: 'Initial prompt',
            },
          ],
        },
      },
    }),
  );
}

function EmitLongActionDisplay({
  backend,
}: {
  backend: AgentBackend;
}): React.JSX.Element {
  useEffect(() => {
    presentLongActionDisplay(backend);
  }, [backend]);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Show action report"
      testID="action-display-harness-reopen"
      onPress={() => presentLongActionDisplay(backend)}
      style={styles.reopen}
    >
      <Text>Show action report</Text>
    </Pressable>
  );
}

export function DesktopActionDisplayHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const backend = useMemo(() => createBackend(), []);

  return (
    <ThemeProvider theme={theme}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          local: {
            status: 'open',
            baseUrl: 'http://local',
            backend: backend as any,
          },
        }}
        connectionNameById={{ local: 'Local agent' }}
      >
        <View testID="desktop-action-display-harness-ready">
          <Text>Action display harness ready</Text>
          <EmitLongActionDisplay backend={backend} />
        </View>
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  reopen: { padding: 16 },
});
