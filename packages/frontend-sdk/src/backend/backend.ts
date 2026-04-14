import type { Event } from '../types/events';
import type { IndexedMessage } from '../types/messages';
import type { SessionSummary } from '../types/sessions';
import type { ConfigSchemaEntry, UiSchemaElement } from '../types/uiSchema';
import type {
  ApplicationActionDefinition,
  ApplicationUiElement,
  ExecuteActionResponse,
} from '../types/plugins';
import type { SessionPluginEntry } from '../types/sessionPlugins';

export interface ListMessagesResult {
  messages: IndexedMessage[];
  cursorEventId: string | null;
  activeRequestId: string | null;
}

export interface FeatureCompletion {
  replacement: string;
  start: number;
  display?: string;
  display_meta?: string;
  [key: string]: any;
}

export interface ListEventsResult {
  events: Event[];
  latestEventId: string | null;
}

export interface BackendCapabilities {
  featureCompletions: boolean;
  sessionUiSchema: boolean;
  sessionConfigOverrides: boolean;
  sessionPlugins: boolean;
  applicationActions: boolean;
  applicationConfig: boolean;
}

export interface AgentBackend {
  readonly kind: 'rest' | 'bridge' | 'inProcess' | (string & {});

  getCapabilities(): BackendCapabilities;

  // --- Agents ---
  listAgents(): Promise<string[]>;
  getSessionAgent(sessionId: string): Promise<string>;
  switchSessionAgent(
    sessionId: string,
    agentId: string,
    options?: { idempotencyKey?: string },
  ): Promise<void>;

  // --- Sessions ---
  createSession(params?: {
    agentId?: string;
    systemMessage?: string;
    idempotencyKey?: string;
  }): Promise<{ session: { session_id: string; [key: string]: any } }>;
  listSessions(params?: { limit?: number }): Promise<SessionSummary[]>;
  forkSession(
    sessionId: string,
    params?: { index?: number; idempotencyKey?: string },
  ): Promise<{ session: { session_id: string; [key: string]: any }; source_session_id: string }>;

  // --- Session plugins ---
  listSessionPlugins(sessionId: string): Promise<SessionPluginEntry[]>;
  setSessionPlugins(
    sessionId: string,
    enabled: string[],
    options?: { idempotencyKey?: string },
  ): Promise<void>;
  clearSessionPlugins(sessionId: string, options?: { idempotencyKey?: string }): Promise<void>;

  // --- Messages ---
  listMessages(
    sessionId: string,
    params?: { start?: number; end?: number },
  ): Promise<ListMessagesResult>;

  appendMessage(
    sessionId: string,
    message: {
      role: 'user' | 'assistant' | 'system' | 'tool';
      content: string;
      multipartContent?: any[] | null;
      metadata?: Record<string, any>;
    },
    options?: { idempotencyKey?: string },
  ): Promise<void>;

  sendMessage(
    sessionId: string,
    params: {
      message: {
        role: 'user' | 'assistant' | 'system' | 'tool';
        content: string;
        multipartContent?: any[] | null;
        metadata?: Record<string, any>;
      };
      configOverrides?: Record<string, any>;
      idempotencyKey?: string;
    },
  ): Promise<{ status?: string; request_id?: string; session_id?: string }>;

  modifyMessage(
    sessionId: string,
    index: number,
    content: string,
    options?: { idempotencyKey?: string },
  ): Promise<void>;

  deleteMessages(
    sessionId: string,
    params: { indices?: number[]; range?: { start?: number; end?: number } },
    options?: { idempotencyKey?: string },
  ): Promise<{ deleted_indices?: number[]; session?: any }>;

  // --- Request lifecycle ---
  send(
    sessionId: string,
    params?: { configOverrides?: Record<string, any>; idempotencyKey?: string },
  ): Promise<{ status?: string; request_id?: string }>;

  cancelRequest(requestId: string, options?: { idempotencyKey?: string }): Promise<void>;

  // --- Events ---
  listEvents(params: {
    sessionId: string;
    sinceId?: string;
    requestId?: string;
    limit?: number;
  }): Promise<ListEventsResult>;
  getLatestEventId(): Promise<string | null>;

  // --- Feature completions (optional) ---
  getFeatureCompletions?(sessionId: string, text: string): Promise<FeatureCompletion[]>;
  applyFeatureCompletion?(
    sessionId: string,
    text: string,
    completion: FeatureCompletion,
  ): Promise<string>;

  // --- UI schema / configuration ---
  getSessionUiSchema(sessionId: string): Promise<UiSchemaElement[]>;
  getSessionOverrides(sessionId: string): Promise<Record<string, any>>;
  patchSessionOverrides(
    sessionId: string,
    values: Record<string, any>,
    options?: { idempotencyKey?: string },
  ): Promise<void>;
  deleteSessionOverride(
    sessionId: string,
    key: string,
    options?: { idempotencyKey?: string },
  ): Promise<void>;
  getSessionConfigSchema(sessionId: string): Promise<ConfigSchemaEntry[]>;
  getSessionBaseConfig(sessionId: string): Promise<Record<string, any>>;

  // --- Application plugins/actions ---
  listApplicationActions(params?: { pluginId?: string }): Promise<ApplicationActionDefinition[]>;
  listApplicationUiSchema(params?: { pluginId?: string }): Promise<ApplicationUiElement[]>;
  getSessionApplicationUiSchema(
    sessionId: string,
    params?: { pluginId?: string },
  ): Promise<ApplicationUiElement[]>;
  executeAction(params: {
    pluginId: string;
    actionId: string;
    actionOwner?: string;
    inputs: Record<string, any>;
    idempotencyKey?: string;
  }): Promise<ExecuteActionResponse>;

  // --- Application-level config (optional; used by terminal today) ---
  getApplicationConfigSchema?(): Promise<Record<string, any>>;
  getApplicationConfig?(): Promise<Record<string, any>>;
  patchApplicationConfig?(values: Record<string, any>): Promise<void>;
}
