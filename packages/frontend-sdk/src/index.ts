export type {
  MessageRole,
  ApiMessage,
  IndexedMessage,
} from './types/messages';

export type { SessionSummary } from './types/sessions';

export type {
  BaseEvent,
  FinalEvent,
  MessageAppendedEvent,
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
  SessionListFieldElement,
  ApplicationUiElement,
  ExecuteActionResponseOk,
  ExecuteActionResponseError,
  ExecuteActionResponse,
} from './types/plugins';

export {
  extractByPath,
  renderTemplate,
  filterFooterElements,
  filterStatusBarElements,
} from './utils/uiSchema';

export { selectDisplayContent } from './utils/messages';

export { parseOptionalInt, parseIndexRangeText } from './utils/range';

export type {
  Transport,
  HttpMethod,
} from './transport/transport';

export { FetchTransport } from './transport/fetchTransport';
export { BridgeTransport } from './transport/bridgeTransport';

export type { BridgeServer, WebSocketLike, WebSocketFactory } from './transport/bridgeTransport';

export type { Subscribable, Unsubscribe } from './util/subscribable';
export { SimpleSubscribable } from './util/subscribable';

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
