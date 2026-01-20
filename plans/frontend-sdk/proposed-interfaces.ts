export type MessageRole = 'system' | 'user' | 'assistant' | 'tool' | (string & {});

export interface ApiMessage {
  role: MessageRole;
  content: string;
  metadata?: Record<string, any> | null;
}

export interface IndexedMessage {
  index: number;
  message: ApiMessage;
}

export interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata?: Record<string, any>;
  pinned?: boolean;
}

export interface BaseEvent {
  event_id: string;
  type: string;
  session_id: string;
  request_id?: string;
  [key: string]: any;
}

export type Event = BaseEvent;

export interface UiSchemaElement {
  ui_type?: string;
  key?: string;
  type?: string;
  label?: string;
  description?: string;
  options?: any;
  data?: string;
  template?: string;
  plugin?: string;
  [k: string]: any;
}

export interface ActionInputParam {
  type?: string;
  required?: boolean;
  default?: any;
  description?: string;
  [k: string]: any;
}

export interface ApplicationActionDefinition {
  plugin: string;
  id: string;
  label?: string;
  description?: string;
  inputs?: Record<string, ActionInputParam>;
  [k: string]: any;
}

export interface ActionUiElement {
  ui_type: string;
  plugin: string;
  id: string;
  label: string;
  icon?: string;
  order?: number;
  action_id: string;
  fixed_params?: Record<string, any>;
  param_map?: Record<string, string>;
  dialog?: any;
  metadata?: Record<string, any>;
  [k: string]: any;
}

export interface SessionListFieldElement {
  ui_type: string;
  plugin: string;
  role?: string;
  data: string;
  template?: string;
  order?: number;
  metadata?: Record<string, any>;
  [k: string]: any;
}

export type ApplicationUiElement =
  | ActionUiElement
  | SessionListFieldElement
  | Record<string, any>;

export interface ExecuteActionResponseOk {
  status: 'ok';
  plugin: string;
  action_id: string;
  result: any;
}

export interface ExecuteActionResponseError {
  status: 'error';
  plugin?: string;
  action_id?: string;
  error_type?: string;
  message?: string;
  details?: any;
}

export type ExecuteActionResponse = ExecuteActionResponseOk | ExecuteActionResponseError;

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

export interface BackendCapabilities {
  featureCompletions: boolean;
  sessionUiSchema: boolean;
  sessionConfigOverrides: boolean;
  applicationActions: boolean;
  applicationConfig: boolean;
}

export interface AgentBackend {
  readonly kind: 'rest' | 'bridge' | 'inProcess' | (string & {});

  getCapabilities(): BackendCapabilities;

  listAgents(): Promise<string[]>;
  getSessionAgent(sessionId: string): Promise<string>;
  switchSessionAgent(sessionId: string, agentId: string): Promise<void>;

  createSession(params?: { agentId?: string; systemMessage?: string }): Promise<{ session: any }>;
  listSessions(params?: { limit?: number }): Promise<SessionSummary[]>;
  forkSession(sessionId: string, params?: { index?: number }): Promise<{ session: any; source_session_id?: string }>;

  listMessages(sessionId: string, params?: { start?: number; end?: number }): Promise<ListMessagesResult>;
  appendMessage(
    sessionId: string,
    message: { role: 'user' | 'assistant' | 'system' | 'tool'; content: string; metadata?: Record<string, any> },
  ): Promise<void>;
  modifyMessage(sessionId: string, index: number, content: string): Promise<void>;
  deleteMessages(
    sessionId: string,
    params: { indices?: number[]; range?: { start?: number; end?: number } },
  ): Promise<{ deleted_indices?: number[]; session?: any }>;

  send(sessionId: string, params?: { configOverrides?: Record<string, any> }): Promise<{ status?: string }>;
  cancelRequest(requestId: string): Promise<void>;

  listEvents(params: {
    sessionId: string;
    sinceId?: string;
    requestId?: string;
    limit?: number;
  }): Promise<Event[]>;

  getFeatureCompletions?(sessionId: string, text: string): Promise<FeatureCompletion[]>;
  applyFeatureCompletion?(sessionId: string, text: string, completion: FeatureCompletion): Promise<string>;

  getSessionUiSchema?(sessionId: string): Promise<UiSchemaElement[]>;
  getSessionOverrides?(sessionId: string): Promise<Record<string, any>>;
  patchSessionOverrides?(sessionId: string, values: Record<string, any>): Promise<void>;
  deleteSessionOverride?(sessionId: string, key: string): Promise<void>;

  listApplicationActions?(params?: { pluginId?: string }): Promise<ApplicationActionDefinition[]>;
  listApplicationUiSchema?(params?: { pluginId?: string }): Promise<ApplicationUiElement[]>;
  executeAction?(params: { pluginId: string; actionId: string; inputs: Record<string, any> }): Promise<ExecuteActionResponse>;

  getApplicationConfigSchema?(): Promise<Record<string, any>>;
  getApplicationConfig?(): Promise<Record<string, any>>;
  patchApplicationConfig?(values: Record<string, any>): Promise<void>;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface Transport {
  request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }>;
}

export interface KeyValueStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  delete(key: string): Promise<void>;
}

export interface Logger {
  debug(...args: any[]): void;
  info(...args: any[]): void;
  warn(...args: any[]): void;
  error(...args: any[]): void;
}

export interface Clock {
  nowMs(): number;
}

export interface Subscribable {
  subscribe(listener: () => void): () => void;
}

export interface ChatState {
  sessionId: string;
  messages: IndexedMessage[];
  cursorEventId: string | null;
  activeRequestId: string | null;
  streaming: null | {
    requestId: string;
    reasoning: string;
    content: string;
    metadata?: Record<string, any> | null;
  };
  error: null | { detail: string; requestId: string | null };
  status: 'idle' | 'loading' | 'ready' | 'sending' | 'error';
}

export interface ChatController extends Subscribable {
  getState(): ChatState;

  loadMessages(params?: { start?: number; end?: number }): Promise<void>;
  appendUserMessage(text: string): Promise<void>;
  send(params?: { text?: string }): Promise<void>;
  resend(): Promise<void>;
  cancelActiveRequest(): Promise<void>;
  modifyMessage(index: number, newText: string): Promise<void>;
  deleteRange(params: { start?: number; end?: number }): Promise<void>;

  startEventStreaming(params?: { initialSinceId?: string | null }): void;
  stopEventStreaming(): void;
}

export interface SessionsState {
  sessions: SessionSummary[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  lastLoadedAtMs: number | null;
}

export interface SessionsController extends Subscribable {
  getState(): SessionsState;
  reload(): Promise<void>;
  createSession(params?: { agentId?: string; systemMessage?: string }): Promise<string>;
}

export interface PluginsState {
  loading: boolean;
  error: string | null;
  actionsById: Record<string, ApplicationActionDefinition>;
  sessionActions: ActionUiElement[];
  messageActions: ActionUiElement[];
  sessionListActions: ActionUiElement[];
  sessionListFields: SessionListFieldElement[];
  sessionListPinnedToggles: ActionUiElement[];
}

export interface PluginsRegistry extends Subscribable {
  getState(): PluginsState;
  ensureLoaded(): Promise<void>;
  invalidate(): void;
}
