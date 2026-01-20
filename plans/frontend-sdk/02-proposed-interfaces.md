# Proposed SDK interfaces (`@crystal-lattice/frontend-sdk`)

This document proposes the public TypeScript surface for the SDK.

Design constraints:

- No imports from `react` or `react-native` in `@crystal-lattice/frontend-sdk`.
- Backend access goes through a stable “Agent backend” interface.
- REST/Bridge backends are just implementations of the backend interface.
- In-process TS backend (future) can implement the same interface.

## 1) Core domain types

These match the shapes used today by the Python HTTP API and the RN app.

```ts
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

export type Event = BaseEvent; // keep permissive; frontends can refine
```

Rationale: the Python server’s event model is intentionally extensible and plugin-driven; the SDK should not prematurely lock this down.

## 2) Backend interface (the key abstraction)

Frontends should depend on this interface only.

```ts
export interface UiSchemaElement {
  ui_type?: string;
  // Config-oriented fields
  key?: string;
  type?: string;
  label?: string;
  description?: string;
  options?: any;
  // Footer / status bar fields
  data?: string;
  template?: string;
  // Plugin / misc
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
  key?: string;
  label?: string;
  description?: string;
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

  // --- Agents ---
  listAgents(): Promise<string[]>;
  getSessionAgent(sessionId: string): Promise<string>;
  switchSessionAgent(sessionId: string, agentId: string): Promise<void>;

  // --- Sessions ---
  createSession(params?: { agentId?: string; systemMessage?: string }): Promise<{ session: any }>;
  listSessions(params?: { limit?: number }): Promise<SessionSummary[]>;
  forkSession(sessionId: string, params?: { index?: number }): Promise<{ session: any; source_session_id?: string }>;

  // --- Messages ---
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

  // --- Request lifecycle ---
  send(sessionId: string, params?: { configOverrides?: Record<string, any> }): Promise<{ status?: string }>;
  cancelRequest(requestId: string): Promise<void>;

  // --- Events ---
  listEvents(params: {
    sessionId: string;
    sinceId?: string;
    requestId?: string;
    limit?: number;
  }): Promise<Event[]>;

  // --- Feature completions (optional; important for editor frontends) ---
  getFeatureCompletions?(sessionId: string, text: string): Promise<FeatureCompletion[]>;
  applyFeatureCompletion?(sessionId: string, text: string, completion: FeatureCompletion): Promise<string>;

  // --- UI schema / configuration (optional; already used by mobile) ---
  getSessionUiSchema?(sessionId: string): Promise<UiSchemaElement[]>;
  getSessionOverrides?(sessionId: string): Promise<Record<string, any>>;
  patchSessionOverrides?(sessionId: string, values: Record<string, any>): Promise<void>;
  deleteSessionOverride?(sessionId: string, key: string): Promise<void>;

  // --- Application plugins/actions (optional; already used by mobile) ---
  listApplicationActions?(params?: { pluginId?: string }): Promise<ApplicationActionDefinition[]>;
  listApplicationUiSchema?(params?: { pluginId?: string }): Promise<ApplicationUiElement[]>;
  executeAction?(params: { pluginId: string; actionId: string; inputs: Record<string, any> }): Promise<ExecuteActionResponse>;

  // --- Application-level config (optional; used by terminal today) ---
  getApplicationConfigSchema?(): Promise<Record<string, any>>;
  getApplicationConfig?(): Promise<Record<string, any>>;
  patchApplicationConfig?(values: Record<string, any>): Promise<void>;
}
```

Notes:

- The “REST” implementation will directly map these methods to the existing HTTP routes.
- The “inProcess” implementation will map to TS `AgentApplication`/`AgentCore` calls (future).
- `getFeatureCompletions` / `applyFeatureCompletion` are optional because today the Python HTTP server does not expose them, but the terminal app already supports them via in-process core. The plan includes adding HTTP endpoints for parity.

## 3) Transport interface (used by REST + Bridge)

This keeps backend implementations portable across runtimes (browser, RN, Node).

```ts
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface Transport {
  request<T = any>(req: {
    method: HttpMethod;
    path: string; // absolute path like "/sessions"
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }>;
}
```

Implementations:

- `HttpTransport({ baseUrl, fetch })`
- `BridgeTransport({ bridgeUrl, pairingToken, serverId, WebSocket })` (Phoenix protocol)

The REST backend can be a thin wrapper around `Transport`.

## 4) Storage + platform services (injected)

SDK modules that persist user data (saved connections, UI preferences, caches) should depend on an injected store.

```ts
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
```

## 5) Headless controllers

Controllers hide complex workflows and expose state + actions. They should not import React; instead use a small subscription mechanism.

### 5.1 Observable pattern

```ts
export interface Subscribable {
  subscribe(listener: () => void): () => void;
}
```

### 5.2 Chat controller

```ts
export interface ChatState {
  sessionId: string;
  messages: IndexedMessage[];
  cursorEventId: string | null;
  activeRequestId: string | null;
  streaming: null | { requestId: string; reasoning: string; content: string; metadata?: Record<string, any> | null };
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
```

Implementation note: the event-application logic currently inside `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` becomes a pure reducer function used by `ChatController`.

### 5.3 Sessions controller

```ts
export interface SessionsState {
  sessions: SessionSummary[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  lastLoadedAtMs: number | null;
}

export interface SessionsController extends Subscribable {
  getState(): SessionsState;
  reload(): Promise<void>;
  createSession(params?: { agentId?: string; systemMessage?: string }): Promise<string>; // returns new session_id
}
```

### 5.4 Plugins registry

```ts
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
```

## 6) Future in-process backend support

To make a TS `agent_core`/`agent_app` backend easy later, the SDK should:

- Keep the `AgentBackend` methods domain-oriented (not HTTP-oriented).
- Keep `Transport` separate and optional.
- Optionally define an *internal* adapter interface for a future TS runtime package to implement, e.g.:

```ts
export interface InProcessAgentRuntime {
  listAgents(): string[];
  createSession(agentId: string, systemMessage?: string): { sessionId: string };
  // ... etc
}
```

The in-process backend can live in a separate package (later), e.g. `@crystal-lattice/agent-runtime-node`, that depends on the TS port of `agent_app`.
