import React, { useEffect, useMemo, useRef } from 'react';
import {StyleSheet, Text, View} from 'react-native';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { SessionSummary } from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '@crystal-lattice/frontend-sdk-react';

import type { MessagesCache, MessagesCacheEntry, SessionsCache } from '../cache/types';
import { ChatPane, type ChatPaneProps } from '../chat/ChatPane';
import type { DesktopSessionTab } from './SessionTabs';
import type { TabStripStyle } from './tabStripStyle';

const RECENT_ACTIVE_TAB_COUNT = 3;

function stringArrayEqual(a: ReadonlyArray<string>, b: ReadonlyArray<string>): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

function deriveMruTabIds(
  previousMruTabIds: ReadonlyArray<string>,
  tabs: ReadonlyArray<DesktopSessionTab>,
  activeTabId: string | null,
): string[] {
  const validTabIds = new Set(tabs.map((tab) => tab.tabId));
  const prunedMruTabIds = previousMruTabIds.filter((tabId) => validTabIds.has(tabId));

  if (activeTabId && validTabIds.has(activeTabId)) {
    return [activeTabId, ...prunedMruTabIds.filter((tabId) => tabId !== activeTabId)];
  }

  return prunedMruTabIds;
}

function deriveWarmTabIds(mruTabIds: ReadonlyArray<string>): string[] {
  return mruTabIds.slice(0, RECENT_ACTIVE_TAB_COUNT).sort();
}

export interface ChatPaneTabStackProps {
  tabs: DesktopSessionTab[];
  activeTabId: string | null;
  styleVariant: TabStripStyle;
  connectionNameById: Record<string, string>;
  getBackend: (connectionId: string) => AgentBackend | null;
  sessionsCache: SessionsCache;
  messagesCache: MessagesCache;
  messagesCacheHydrated?: boolean;
  onUpdateCache: ChatPaneProps['onUpdateCache'];
  onOpenSessionTab: (params: {
    connectionId: string;
    sessionId: string;
    title?: string;
    subtitle?: string | null;
  }) => void;
}

type TabFrameProps = {
  tabId: string;
  isVisible: boolean;
  isActive: boolean;
  connectionId: string;
  connectionName: string;
  sessionId: string;
  title: string;
  subtitle?: string;
  styleVariant: TabStripStyle;
  backend: AgentBackend | null;
  sessionSummary: SessionSummary | null;
  cachedEntry: MessagesCacheEntry | null;
  messagesCacheHydrated?: boolean;
  onUpdateCache: ChatPaneTabStackProps['onUpdateCache'];
  onOpenSessionTab: ChatPaneTabStackProps['onOpenSessionTab'];
};

const TabFrame = React.memo(function TabFrame(props: TabFrameProps): React.JSX.Element {
  const {
    isVisible,
    isActive,
    connectionId,
    connectionName,
    sessionId,
    sessionSummary,
    title,
    subtitle,
    styleVariant,
    backend,
    cachedEntry,
    messagesCacheHydrated,
    onUpdateCache,
    onOpenSessionTab,
  } = props;

  return (
    <View
      style={[styles.frame, isVisible ? styles.visible : styles.hidden, isActive ? styles.active : styles.inactive]}
      pointerEvents={isVisible ? 'auto' : 'none'}
    >
      <ApplicationPluginsProvider backend={backend} connectionId={connectionId}>
        <ChatPane
          isVisible={isVisible}
          isActive={isActive}
          connectionId={connectionId}
          connectionName={connectionName}
          sessionId={sessionId}
          sessionSummary={sessionSummary}
          title={title}
          subtitle={subtitle}
          styleVariant={styleVariant}
          backend={backend}
          cachedEntry={cachedEntry}
          messagesCacheHydrated={messagesCacheHydrated}
          onUpdateCache={onUpdateCache}
          onOpenSessionTab={onOpenSessionTab}
        />
      </ApplicationPluginsProvider>
    </View>
  );
});

export function ChatPaneTabStackPlaceholder(props: ChatPaneTabStackProps): React.JSX.Element {

  return <View><Text>Placeholder</Text></View>
}

export function ChatPaneTabStack(props: ChatPaneTabStackProps): React.JSX.Element {
  const {
    tabs,
    activeTabId,
    styleVariant,
    connectionNameById,
    getBackend,
    sessionsCache,
    messagesCache,
    messagesCacheHydrated,
    onUpdateCache,
    onOpenSessionTab,
  } = props;
  
  // Keep MRU ordering in a ref so switching among already-active tabs
  // doesn't force a second render from state updates.
  const mruTabIdsRef = useRef<string[]>(activeTabId ? [activeTabId] : []);
  const { nextMruTabIds, warmTabIds } = useMemo(() => {
    const nextMru = deriveMruTabIds(mruTabIdsRef.current, tabs, activeTabId);
    return {
      nextMruTabIds: nextMru,
      warmTabIds: deriveWarmTabIds(nextMru),
    };
  }, [activeTabId, tabs]);

  useEffect(() => {
    if (stringArrayEqual(mruTabIdsRef.current, nextMruTabIds)) {
      return;
    }
    mruTabIdsRef.current = nextMruTabIds;
  }, [nextMruTabIds]);

  const warmSet = useMemo(() => new Set(warmTabIds), [warmTabIds]);
  const renderedTabs = useMemo(
    () => tabs.filter((tab) => warmSet.has(tab.tabId)),
    [tabs, warmSet],
  );

  return (
    <View style={styles.stack}>
      {renderedTabs.map((tab) => {
        const connectionName = connectionNameById[tab.connectionId] ?? tab.connectionId;
        const backend = getBackend(tab.connectionId);
	        const sessionSummary =
	          (sessionsCache[tab.connectionId]?.sessions ?? []).find(
	            (session) => session.session_id === tab.sessionId,
	          ) ?? null;
        const cachedEntry = messagesCache[tab.connectionId]?.[tab.sessionId] ?? null;
        const isVisible = tab.tabId === activeTabId;
        const isActive = isVisible || warmSet.has(tab.tabId);

        return (
          <TabFrame
            key={tab.tabId}
            tabId={tab.tabId}
            isVisible={isVisible}
            isActive={isActive}
            connectionId={tab.connectionId}
            connectionName={connectionName}
            sessionId={tab.sessionId}
            sessionSummary={sessionSummary}
            title={tab.title}
            subtitle={tab.subtitle ?? undefined}
            styleVariant={styleVariant}
            backend={backend}
            cachedEntry={cachedEntry}
            messagesCacheHydrated={messagesCacheHydrated}
            onUpdateCache={onUpdateCache}
            onOpenSessionTab={onOpenSessionTab}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  stack: {
    flex: 1,
  },
  frame: {
    ...StyleSheet.absoluteFillObject,
  },
  visible: {
    opacity: 1,
    //zIndex: 1,
  },
  hidden: {
    //display: 'none'
    opacity: 0,
    //zIndex: 0,
  },
  active: {

  },
  inactive: {
    display: 'none',
  }
});
