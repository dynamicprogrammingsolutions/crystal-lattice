export type {
  MessageRole,
  ApiMessage,
  IndexedMessage,
} from './types/messages';

export type { SessionSummary } from './types/sessions';

export type { SessionPluginEntry } from './types/sessionPlugins';

export type {
  BaseEvent,
  SessionCreatedEvent,
  FinalEvent,
  MessageAppendedEvent,
  MessageModifiedEvent,
  MessagesDeletedEvent,
  ToolResultsEvent,
  RequestCompletedEvent,
  RequestStartedEvent,
  ErrorEvent,
  AssistantMessageEvent,
  PartialEvent,
  CheckpointEvent,
  Event,
} from './types/events';

export type {
  UiSchemaElement,
  ConfigSchemaEntry,
} from './types/uiSchema';

export type {
  ActionInputParam,
  ApplicationActionDefinition,
  ActionUiElement,
  ActionMutations,
  ActionUiEffects,
  StandardActionResult,
  SessionListFieldElement,
  ApplicationUiElement,
  ExecuteActionResponseOk,
  ExecuteActionResponseError,
  ExecuteActionResponse,
} from './types/plugins';

export {
  extractByPath,
  renderTemplate,
  formatValueForElement,
  filterFooterElements,
  filterStatusBarElements,
  evaluateCondition,
} from './utils/uiSchema';

export { selectDisplayContent, selectSingleLineContent } from './utils/messages';

export { parseOptionalInt, parseIndexRangeText } from './utils/range';

export type {
  Transport,
  HttpMethod,
} from './transport/transport';

export type { KeyValueStore } from './storage/keyValueStore';

export { FetchTransport } from './transport/fetchTransport';
export { BridgeTransport } from './transport/bridgeTransport';

export type { BridgeServer, WebSocketLike, WebSocketFactory } from './transport/bridgeTransport';

export type { Subscribable, Unsubscribe } from './util/subscribable';
export { SimpleSubscribable } from './util/subscribable';

export type { SdkEvent } from './runtime/sdkEvent';
export type { SdkEventBusSnapshot } from './runtime/sdkEventBus';
export { SdkEventBus } from './runtime/sdkEventBus';
export type { SdkRuntimeOptions } from './runtime/sdkRuntime';
export { SdkRuntime } from './runtime/sdkRuntime';
export type {
  BackendCallContext,
  BackendCallNext,
  BackendMiddleware,
  MethodSuccessEventMiddlewareOptions,
} from './runtime/eventedBackend';
export {
  createEventedBackend,
  createMethodSuccessEventMiddleware,
} from './runtime/eventedBackend';
export { BusAwareController } from './runtime/busAwareController';

export {
  SESSION_MUTATION_EVENT_TYPES,
  type SessionMutationEventType,
  type SessionScopedSdkEvent,
  type SessionPluginsChangedEvent,
  type SessionOverridesChangedEvent,
  type SessionAgentChangedEvent,
  type SessionSummaryUpsertedEvent,
  type SessionMutationEvent,
} from './sessionMutations/sessionMutationEventTypes';
export {
  createSessionScopedSuccessEventMiddleware,
  type SessionScopedSuccessEventMiddlewareOptions,
} from './sessionMutations/createSessionScopedSuccessEventMiddleware';
export {
  DEFAULT_SESSION_MUTATION_MIDDLEWARES,
  createDefaultSessionMutationMiddlewares,
} from './sessionMutations/sessionMutationMiddlewares';
export { isEventForSession } from './sessionMutations/sessionMutationRules';

export type { CreateDefaultBackendMiddlewaresOptions } from './runtimeFactory/createDefaultBackendMiddlewares';
export { createDefaultBackendMiddlewares } from './runtimeFactory/createDefaultBackendMiddlewares';
export type { CreateDefaultSdkRuntimeOptions } from './runtimeFactory/createDefaultSdkRuntime';
export { createDefaultSdkRuntime } from './runtimeFactory/createDefaultSdkRuntime';

export type { AgentsControllerState } from './agents/agentsController';
export { AgentsController, pickDefaultAgentId } from './agents/agentsController';

export type { PollingStatus, PollingEventSourceOptions } from './events/pollingEventSource';
export { PollingEventSource } from './events/pollingEventSource';

export type { PluginsResult, PluginsRegistryState } from './plugins/pluginsRegistry';
export { PluginsRegistry } from './plugins/pluginsRegistry';

export type { ActionEffect, RunActionResult, RunActionContext, RunActionEffectsOptions } from './plugins/actionRunner';
export { runApplicationAction, getRunActionErrorMessage } from './plugins/actionRunner';

export type { SessionsControllerState } from './sessions/sessionsController';
export { SessionsController } from './sessions/sessionsController';

export type {
  SessionListFieldGroups,
  SessionListPresentation,
} from './sessions/sessionListPresentation';
export {
  groupSessionListFields,
  deriveSessionListPresentation,
  deriveSessionListPresentationFromGroups,
} from './sessions/sessionListPresentation';

export type { ChatControllerState, StreamingRow, RequestErrorState } from './chat/chatController';
export { ChatController } from './chat/chatController';

export { selectLastAssistantMessage, deriveChatStatusBarParts } from './chat/presentation';

export type { SessionUiSchemaControllerState } from './uiSchema/sessionUiSchemaController';
export { SessionUiSchemaController } from './uiSchema/sessionUiSchemaController';

export type {
  AgentBackend,
  BackendCapabilities,
  ListMessagesResult,
  FeatureCompletion,
} from './backend/backend';

export { RestAgentBackend } from './backend/restBackend';

export type {
  ConnectionKind,
  BaseConnectionRecord,
  ManualConnectionRecord,
  DiscoveryConnectionRecord,
  BridgeConnectionRecord,
  ConnectionRecord,
} from './connections/types';

export { CONNECTIONS_STORAGE_KEY, loadConnections, saveConnections } from './connections/store';
