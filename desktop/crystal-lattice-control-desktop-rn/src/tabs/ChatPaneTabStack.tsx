import React, { useEffect, useMemo, useRef, useState } from 'react';
import {StyleSheet, Text, View} from 'react-native';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { SessionSummary } from '@crystal-lattice/frontend-sdk';
import type { SdkRuntime } from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider, SdkRuntimeProvider } from '@crystal-lattice/frontend-sdk-react';

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

export interface ChatPaneTabStackProps {
  tabs: DesktopSessionTab[];
  activeTabId: string | null;
  styleVariant: TabStripStyle;
  connectionNameById: Record<string, string>;
  getBackend: (connectionId: string) => AgentBackend | null;
  getRuntime: (connectionId: string) => SdkRuntime | null;
  sessionsCache: SessionsCache;
  messagesCache: MessagesCache;
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
  runtime: SdkRuntime | null;
  sessionSummary: SessionSummary | null;
  cachedEntry: MessagesCacheEntry | null;
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
    runtime,
    cachedEntry,
    onUpdateCache,
    onOpenSessionTab,
  } = props;

  return (
    <View
      style={[styles.frame, isVisible ? styles.visible : styles.hidden, isActive ? styles.active : styles.inactive]}
      pointerEvents={isVisible ? 'auto' : 'none'}
    >
      <SdkRuntimeProvider runtime={runtime}>
      <ApplicationPluginsProvider>
        <ChatPane
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
          onUpdateCache={onUpdateCache}
          onOpenSessionTab={onOpenSessionTab}
        />
      </ApplicationPluginsProvider>
      </SdkRuntimeProvider>
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
    getRuntime,
    sessionsCache,
    messagesCache,
    onUpdateCache,
    onOpenSessionTab,
  } = props;
  
  // Keep MRU ordering in a ref so switching among already-active tabs
  // doesn't force a second render from state updates.
  const mruTabIdsRef = useRef<string[]>(activeTabId ? [activeTabId] : []);
  // State only tracks membership (not ordering) of the warm set.
  const warmTabIdsRef = useRef<string[]>(activeTabId ? [activeTabId] : []);
  const [warmTabIds, setWarmTabIds] = useState<string[]>(() => (activeTabId ? [activeTabId] : []));

  useEffect(() => {
    const valid = new Set(tabs.map((tab) => tab.tabId));

    const pruned = mruTabIdsRef.current.filter((id) => valid.has(id));
    if (activeTabId && valid.has(activeTabId)) {
      mruTabIdsRef.current = [activeTabId, ...pruned.filter((id) => id !== activeTabId)];
    } else {
      mruTabIdsRef.current = pruned;
    }

    const nextWarm = mruTabIdsRef.current.slice(0, RECENT_ACTIVE_TAB_COUNT).sort();
    if (!stringArrayEqual(nextWarm, warmTabIdsRef.current)) {
      warmTabIdsRef.current = nextWarm;
    }
    //setWarmTabIds((prev) => (stringArrayEqual(prev, nextWarm) ? prev : nextWarm));
  }, [activeTabId, tabs]);

  const warmSet = useMemo(() => new Set(warmTabIdsRef.current), [warmTabIdsRef.current]);

  return (
    <View style={styles.stack}>
      {tabs.map((tab) => {
        const connectionName = connectionNameById[tab.connectionId] ?? tab.connectionId;
        const backend = getBackend(tab.connectionId);
	      const runtime = getRuntime(tab.connectionId);
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
	          runtime={runtime}
            cachedEntry={cachedEntry}
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
