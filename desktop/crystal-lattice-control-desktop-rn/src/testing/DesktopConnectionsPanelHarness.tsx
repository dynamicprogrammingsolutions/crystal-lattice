import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MARKDOWN_BASE_FONT_SIZES,
  ThemeProvider,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';

import {
  ConnectionsPanel,
  getConnectionsListMaxHeight,
} from '../panels/ConnectionsPanel';
import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from '../windows/desktopWindowManager';

interface DesktopConnectionsPanelHarnessProps {
  connectionsHarnessCount?: unknown;
  connectionsHarnessPreset?: unknown;
}

function normalizeCount(value: unknown): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : 0;
}

function buildConnections(count: number): ConnectionRecord[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `harness-connection-${index + 1}`,
    kind: 'manual' as const,
    name: `Harness connection ${index + 1}`,
    host: '127.0.0.1',
    port: 8100 + index,
    lastUsedAt: count - index,
  }));
}

export function DesktopConnectionsPanelHarness({
  connectionsHarnessCount,
  connectionsHarnessPreset,
}: DesktopConnectionsPanelHarnessProps): React.JSX.Element {
  const baseTheme = useDesktopTheme();
  const count = normalizeCount(connectionsHarnessCount);
  const baseFontSize =
    connectionsHarnessPreset === 'largest'
      ? MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1]
      : DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize;
  const theme = useMemo(
    () => applyDisplayTypographyPreset(baseTheme, baseFontSize),
    [baseFontSize, baseTheme],
  );
  const records = useMemo(() => buildConnections(count), [count]);
  const [panelHeight, setPanelHeight] = useState<number | null>(null);

  useEffect(() => {
    if (panelHeight === null) {
      return;
    }
    DesktopWindowManager?.recordConnectionsPanelHarnessState?.({
      count,
      preset: connectionsHarnessPreset === 'largest' ? 'largest' : 'default',
      baseFontSize,
      panelHeight,
      expectedListMaxHeight: getConnectionsListMaxHeight(theme),
      expectedTitleLineHeight: theme.typography.lineHeight.secondary,
      expectedMetadataLineHeight: theme.typography.lineHeight.tiny,
    });
  }, [
    baseFontSize,
    connectionsHarnessPreset,
    count,
    panelHeight,
    theme,
  ]);

  return (
    <ThemeProvider theme={theme}>
      <View style={[styles.root, { backgroundColor: theme.background }]}>
        <View
          testID="connections-harness-panel-frame"
          onLayout={(event) =>
            setPanelHeight(event.nativeEvent.layout.height)
          }
        >
          <ConnectionsPanel
            connectionRecords={records}
            focusedConnectionId={records[0]?.id ?? null}
            openConnectionsById={{}}
            rowClickBehavior="focusOnly"
            onFocusConnection={() => {}}
            onOpenConnection={() => {}}
            onCloseConnection={() => {}}
            onDeleteConnection={() => {}}
            onClearConnections={() => {}}
            onOpenNewConnectionEditor={() => {}}
            onOpenEditConnectionEditor={() => {}}
          />
        </View>
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    padding: 24,
  },
});