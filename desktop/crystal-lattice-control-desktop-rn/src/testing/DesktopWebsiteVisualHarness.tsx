import React, { useMemo } from 'react';
import { Settings, StyleSheet, useColorScheme, View } from 'react-native';

import type {
  AgentBackend,
  AgentDescriptor,
  IndexedMessage,
  SessionSummary,
  SessionPluginEntry,
} from '@crystal-lattice/frontend-sdk';
import { ApplicationPluginsProvider } from '@crystal-lattice/frontend-sdk-react';
import {
  ThemeProvider,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';

import { ChatPane } from '../chat/ChatPane';
import { buildDesktopCaptureTheme } from '../theme/buildDesktopTheme';
import { AgentPickerWindow } from '../windows/AgentPickerWindow';

const SESSION_ID = 'website-visual-session';
const CONNECTION_ID = 'website-visual';

const AGENT_DESCRIPTORS: AgentDescriptor[] = [
  {
    id: 'codex-openai',
    title: 'Codex · OpenAI',
    description: 'Codex-style tools with automatic OpenAI authentication.',
    order: 10,
  },
  {
    id: 'claude-anthropic',
    title: 'Claude · Anthropic',
    description: 'Claude-oriented tools with native Anthropic controls.',
    order: 20,
  },
  {
    id: 'gemini',
    title: 'Gemini',
    description: 'Gemini-oriented tools with search and file workflows.',
    order: 30,
  },
  {
    id: 'qwen',
    title: 'Qwen',
    description: 'Qwen-oriented instructions and tool conventions.',
    order: 40,
  },
  {
    id: 'kimi',
    title: 'Kimi',
    description: 'Kimi-oriented research guidance and compaction.',
    order: 50,
  },
  {
    id: 'grok',
    title: 'Grok',
    description: 'Grok-oriented instructions with web and file tools.',
    order: 60,
  },
];

function tool(
  id: string,
  name: string,
): SessionPluginEntry {
  return {
    id,
    kind: 'tools',
    name,
    class_path: `website_visual.${id}`,
    enabled: true,
    active: true,
    source: 'agent',
  };
}

const CODEX_TOOLS: SessionPluginEntry[] = [
  tool('codex_apply_patch_tool', 'Apply patch'),
  tool('codex_shell_tool', 'Shell'),
  tool('codex_view_image_tool', 'View image'),
  tool('codex_read_file_tool', 'Read file'),
];

const CLAUDE_TOOLS: SessionPluginEntry[] = [
  tool('claude_read_tool', 'Read'),
  tool('claude_write_tool', 'Write'),
  tool('claude_edit_tool', 'Edit'),
  tool('claude_glob_tool', 'Glob'),
  tool('claude_grep_tool', 'Grep'),
  tool('claude_bash_tool', 'Bash'),
];

const CONTINUITY_SESSION_ID = 'dc4efaec-9451-5981-a721-175a079860fb';
const CONTINUITY_SUMMARY: SessionSummary = {
  session_id: CONTINUITY_SESSION_ID,
  modified: 1,
  preview:
    'After upgrading Starlette, one of our custom GZipResponder subclasses stopped',
  metadata: {
    agent_id: 'codex-openai',
    status: 'in_progress',
  },
  presentation: {
    title: 'Plan a Starlette compatibility fix',
    subtitle: 'Coding session · OpenAI Responses',
    meta: 'Status: In progress',
  },
};
const CONTINUITY_MESSAGES: IndexedMessage[] = [
  {
    index: 5,
    message: {
      role: 'user',
      content:
        'Compare the direct default and shared-constant fixes. Which approach would you choose, and why?',
      metadata: {},
    },
  },
  {
    index: 6,
    message: {
      role: 'assistant',
      content:
        'I would choose **adding the default directly to `GZipResponder`**. It restores backwards compatibility with the smallest patch and review surface, while a focused regression test can guard against future default drift.',
      metadata: {
        reasoning: '**Choosing the smallest backwards-compatible fix**',
        usage_total_cost_cumulative_formatted: '$0.018577',
        usage_effective_auth_mode_label: 'ChatGPT',
      },
    },
  },
];

function createBackend(plugins: SessionPluginEntry[]): AgentBackend {
  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: true,
      applicationActions: false,
      applicationConfig: false,
    }),
    listAgents: async () => AGENT_DESCRIPTORS.map(agent => agent.id),
    listAgentDescriptors: async () => AGENT_DESCRIPTORS,
    listAgentPlugins: async () => plugins,
    getSessionAgent: async () => AGENT_DESCRIPTORS[0].id,
    switchSessionAgent: async () => {},
    createSession: async () => ({ session: { session_id: SESSION_ID } }),
    listSessions: async () => [],
    getSessionSummary: async () => ({
      session_id: SESSION_ID,
      modified: 1,
      preview: 'Website visual session',
      metadata: {},
    }),
    listSessionPlugins: async () => plugins,
    setSessionPlugins: async () => {},
    clearSessionPlugins: async () => {},
  } as unknown as AgentBackend;
}

function createContinuityBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ['codex-openai'],
    listAgentDescriptors: async () => [AGENT_DESCRIPTORS[0]],
    getSessionAgent: async () => 'codex-openai',
    switchSessionAgent: async () => {},
    listSessions: async () => [CONTINUITY_SUMMARY],
    getSessionSummary: async () => CONTINUITY_SUMMARY,
    listMessages: async () => ({
      messages: CONTINUITY_MESSAGES,
      cursorEventId: '0',
      activeRequestId: null,
    }),
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
    getSessionUiSchema: async () => [],
    getSessionApplicationUiSchema: async () => [],
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getSessionOverrides: async () => ({}),
    patchSessionOverrides: async () => {},
    deleteSessionOverride: async () => {},
    getSessionConfigSchema: async () => [],
    getSessionBaseConfig: async () => ({}),
    listSessionSnapshots: async () => [],
    getSelectedSessionSnapshot: async () => null,
    listSessionNotifications: async () => [],
    listApplicationNotifications: async () => [],
  } as unknown as AgentBackend;
}

function DesktopContinuityVisual({
  theme,
}: {
  theme: Theme;
}): React.JSX.Element {
  const backend = useMemo(() => createContinuityBackend(), []);
  return (
    <ThemeProvider theme={theme}>
      <ApplicationPluginsProvider
        backend={backend}
        connectionId={CONNECTION_ID}
      >
        <View style={styles.continuityRoot}>
          <ChatPane
            isVisible
            isActive
            connectionId={CONNECTION_ID}
            connectionName="Local workspace"
            sessionId={CONTINUITY_SESSION_ID}
            sessionSummary={CONTINUITY_SUMMARY}
            title="Plan a Starlette compatibility fix"
            backend={backend}
            cachedEntry={{
              connectionId: CONNECTION_ID,
              sessionId: CONTINUITY_SESSION_ID,
              messages: CONTINUITY_MESSAGES,
              cursorEventId: '0',
              activeRequestId: null,
              lastLoadedAt: 1,
              rangeStartText: '-50',
              rangeEndText: '',
              composeText: '',
              scrollAnchor: null,
            }}
            onUpdateCache={() => {}}
          />
        </View>
      </ApplicationPluginsProvider>
    </ThemeProvider>
  );
}

export interface DesktopWebsiteVisualHarnessProps {
  websiteVisualKind?: 'agent-codex' | 'agent-claude' | string;
}

export function DesktopWebsiteVisualHarness({
  websiteVisualKind = 'agent-codex',
}: DesktopWebsiteVisualHarnessProps): React.JSX.Element {
  const systemAppearance = useColorScheme() === 'dark' ? 'dark' : 'light';
  const configuredAppearance = Settings.get('clcWebsiteVisualTheme');
  const appearance =
    configuredAppearance === 'dark' || configuredAppearance === 'light'
      ? configuredAppearance
      : systemAppearance;
  const theme = useMemo(
    () => buildDesktopCaptureTheme(appearance),
    [appearance],
  );
  const claude = websiteVisualKind === 'agent-claude';
  const backend = useMemo(
    () => createBackend(claude ? CLAUDE_TOOLS : CODEX_TOOLS),
    [claude],
  );
  if (websiteVisualKind === 'cross-device') {
    return <DesktopContinuityVisual theme={theme} />;
  }
  const selectedAgentId = claude ? 'claude-anthropic' : 'codex-openai';

  return (
    <View
      style={styles.root}
      testID="desktop-website-visual-harness-ready"
      accessibilityLabel={`Desktop website visual ${websiteVisualKind}`}
    >
      <AgentPickerWindow
        connectionId={CONNECTION_ID}
        connectionName="Local workspace"
        agents={AGENT_DESCRIPTORS.map(agent => agent.id)}
        agentDescriptors={AGENT_DESCRIPTORS}
        backend={backend}
        themeOverride={theme}
        initialAgentId={selectedAgentId}
        title="Choose an agent"
        primaryButtonLabel="Use agent"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  continuityRoot: {
    flex: 1,
  },
});