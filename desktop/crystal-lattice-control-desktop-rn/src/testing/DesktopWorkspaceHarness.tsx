import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  ThemeProvider,
  deriveHomeSessionCollections,
  moveReorderValues,
} from '@crystal-lattice/frontend-rn-components';
import type {
  ConnectionRecord,
  SessionRequestStatus,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import {
  DesktopActivityRail,
  type DesktopLowerPanel,
} from '../layout/DesktopActivityRail';
import { DesktopShell } from '../layout/DesktopShell';
import { DesktopHomeView } from '../home/DesktopHomeView';
import { HistoryPanel } from '../panels/HistoryPanel';
import { SessionTabs } from '../tabs/SessionTabs';
import type { DesktopSessionTab } from '../tabs/desktopWorkspaceState';
import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from '../windows/desktopWindowManager';

const connection = {
  id: 'harness-connection',
  kind: 'manual',
  name: 'Harness server',
  host: '127.0.0.1',
  port: 9000,
} as ConnectionRecord;

const summaries: SessionSummary[] = [
  {
    session_id: 'one',
    modified: Date.now() / 1000,
    preview: 'First session',
  },
  {
    session_id: 'two',
    modified: Date.now() / 1000 - 10,
    preview: 'Second session',
  },
  {
    session_id: 'preview',
    modified: Date.now() / 1000 - 20,
    preview: 'Preview session',
  },
];

function tab(sessionId: string): DesktopSessionTab {
  const summary = summaries.find(
    candidate => candidate.session_id === sessionId,
  )!;
  return {
    tabId: `${connection.id}:${sessionId}`,
    connectionId: connection.id,
    sessionId,
    title: summary.preview,
    subtitle: connection.name,
  };
}

const requestStatus: SessionRequestStatus = {
  session_id: 'preview',
  request_id: 'request',
  state: 'running',
  basis: 'active_request',
  session_modified: summaries[2].modified,
};

export function DesktopWorkspaceHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const [permanentTabs, setPermanentTabs] = useState([tab('one'), tab('two')]);
  const [previewTab, setPreviewTab] = useState<DesktopSessionTab | null>(
    tab('preview'),
  );
  const [active, setActive] = useState<string>('harness-connection:preview');
  const [homeActive, setHomeActive] = useState(false);
  const [connectionsVisible, setConnectionsVisible] = useState(true);
  const [lowerPanel, setLowerPanel] = useState<DesktopLowerPanel>('sessions');
  const [watchlist, setWatchlist] = useState([
    { connectionId: connection.id, sessionId: 'one' },
    { connectionId: connection.id, sessionId: 'two' },
  ]);
  const collections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections: [connection],
        sessionsCache: {
          [connection.id]: { sessions: summaries },
        },
        watchlist,
        notes: { one: 'Harness note' },
        recentSessionsWindow: '3d',
      }),
    [watchlist],
  );
  const statuses = {
    [connection.id]: { preview: requestStatus },
  };

  useEffect(() => {
    DesktopWindowManager?.recordDesktopWorkspaceHarnessState?.({
      permanentOrder: permanentTabs.map(item => item.sessionId),
      previewSessionId: previewTab?.sessionId ?? null,
      active: homeActive ? 'home' : active,
      connectionsVisible,
      lowerPanel,
      watchlistOrder: watchlist.map(item => item.sessionId),
    });
  }, [
    active,
    connectionsVisible,
    homeActive,
    lowerPanel,
    permanentTabs,
    previewTab,
    watchlist,
  ]);

  return (
    <ThemeProvider theme={theme}>
      <DesktopShell
        activityRail={
          <DesktopActivityRail
            connectionsVisible={connectionsVisible}
            lowerPanel={lowerPanel}
            onToggleConnections={() =>
              setConnectionsVisible(current => !current)
            }
            onSelectLowerPanel={setLowerPanel}
          />
        }
        panel={
          <View style={styles.panel}>
            {connectionsVisible ? (
              <Text accessibilityLabel="Harness Connections panel">
                Connections
              </Text>
            ) : null}
            {lowerPanel === 'sessions' ? (
              <Text accessibilityLabel="Harness Sessions panel">Sessions</Text>
            ) : (
              <HistoryPanel
                collections={collections}
                statuses={statuses}
                doubleClickAction="preview"
                onOpenSession={() => {}}
                onToggleWatch={() => {}}
                onEditNote={() => {}}
              />
            )}
          </View>
        }
        main={
          <View style={styles.main}>
            <SessionTabs
              permanentTabs={permanentTabs}
              previewTab={previewTab}
              homeActive={homeActive}
              activeTabId={homeActive ? null : active}
              styleVariant="toolbarTabs"
              connectionNameById={{ [connection.id]: connection.name }}
              requestStatuses={statuses}
              onSelectHome={() => setHomeActive(true)}
              onSelectTab={tabId => {
                setHomeActive(false);
                setActive(tabId);
              }}
              onCloseTab={tabId => {
                if (previewTab?.tabId === tabId) {
                  setPreviewTab(null);
                  setHomeActive(true);
                } else {
                  setPermanentTabs(current =>
                    current.filter(item => item.tabId !== tabId),
                  );
                }
              }}
              onPromotePreview={() => {
                if (!previewTab) return;
                setPermanentTabs(current => [...current, previewTab]);
                setPreviewTab(null);
              }}
              onReorderPermanent={(fromIndex, toIndex) =>
                setPermanentTabs(current =>
                  moveReorderValues(current, fromIndex, toIndex),
                )
              }
            />
            <View style={styles.content}>
              {homeActive ? (
                <DesktopHomeView
                  collections={collections}
                  statuses={statuses}
                  doubleClickAction="preview"
                  onOpenSession={() => {}}
                  onToggleWatch={() => {}}
                  onEditNote={() => {}}
                  onMoveWatchlistItem={(fromIndex, toIndex) =>
                    setWatchlist(current =>
                      moveReorderValues(current, fromIndex, toIndex),
                    )
                  }
                />
              ) : (
                <Text accessibilityLabel={`Harness Active ${active}`}>
                  {active}
                </Text>
              )}
            </View>
          </View>
        }
      />
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  panel: {
    flex: 1,
    padding: 12,
    gap: 12,
  },
  main: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 12,
  },
});
