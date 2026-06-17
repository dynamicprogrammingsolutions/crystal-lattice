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
  ActionDisplayOpenUrlAction,
  ActionDisplayCopyTextAction,
  ActionDisplayRunActionAction,
  ActionDisplayDownloadAttachmentAssetAction,
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
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
  coerceValueForElement,
  filterFooterElements,
  filterStatusBarElements,
  evaluateCondition,
} from './utils/uiSchema';

export { selectDisplayContent, selectSingleLineContent } from './utils/messages';

export { parseOptionalInt, parseIndexRangeText } from './utils/range';
export { generateIdempotencyKey } from './utils/idempotency';
export { selectAttachmentPreviewUrl } from './attachments/preview';
export type { AttachmentDraftStatus } from './attachments/draftStatus';
export { isAttachmentDraftBlocking, attachmentDraftStatusLabel } from './attachments/draftStatus';

export type {
  Transport,
  HttpMethod,
  PathPrefixTimeoutRule,
  TransportTimeoutRule,
} from './transport/transport';

export type { KeyValueStore } from './storage/keyValueStore';
export type {
  SessionScopedMessagesCacheEntry,
  SessionScopedMessagesBySession,
  SessionScopedMessagesCache,
  SessionScopedMessagesCacheIndexEntry,
  SessionScopedMessagesCacheHydrationResult,
} from './storage/sessionScopedMessagesCache';

export { FetchTransport } from './transport/fetchTransport';
export { BridgeTransport } from './transport/bridgeTransport';
export {
  CloudTransport,
  formatCloudConnectionLink,
  parseCloudConnectionLink,
} from './transport/cloudTransport';

export type { BridgeServer, WebSocketLike, WebSocketFactory } from './transport/bridgeTransport';
export type { CloudConnectionLink } from './transport/cloudTransport';

export type { Subscribable, Unsubscribe } from './util/subscribable';
export { SimpleSubscribable } from './util/subscribable';

export type { AgentsControllerState } from './agents/agentsController';
export { AgentsController, pickDefaultAgentId } from './agents/agentsController';

export type { PollingStatus, PollingEventSourceOptions } from './events/pollingEventSource';
export { PollingEventSource } from './events/pollingEventSource';

export type { PluginsResult, PluginsRegistryState } from './plugins/pluginsRegistry';
export { PluginsRegistry } from './plugins/pluginsRegistry';
export type { SessionScopedActionUiType } from './plugins/actionSources';
export {
  mergeSessionScopedActionElements,
  selectSessionScopedActionElements,
} from './plugins/actionSources';

export type { ActionEffect, RunActionResult, RunActionContext, RunActionEffectsOptions } from './plugins/actionRunner';
export { runApplicationAction, getRunActionErrorMessage } from './plugins/actionRunner';
export type { ActionDisplayHost, ActionDisplaySurface } from './plugins/actionDisplayPolicy';
export { normalizeActionDisplayForSurface } from './plugins/actionDisplayPolicy';
export type {
  ComposerAttachmentUiElement,
  SessionAssetRef,
  StoredAttachmentAssetDescriptor,
  DownloadedAttachmentPayload,
} from './plugins/attachmentActions';
export {
  DEFAULT_ATTACHMENT_ACTION_OWNER,
  SESSION_ASSET_ATTACHMENTS_PLUGIN_ID,
  STORE_ATTACHMENT_ACTION_ID,
  DELETE_ATTACHMENT_ACTION_ID,
  DOWNLOAD_ATTACHMENT_ACTION_ID,
  selectSessionAssetId,
  resolveAttachmentActionPluginId,
  storeSessionAttachment,
  deleteSessionAttachment,
  downloadSessionAttachment,
} from './plugins/attachmentActions';

export type { SessionsControllerState } from './sessions/sessionsController';
export { SessionsController } from './sessions/sessionsController';

export type { SessionContextControllerState } from './sessions/sessionContextController';
export { SessionContextController } from './sessions/sessionContextController';

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

export type { SessionApplicationUiSchemaControllerState } from './uiSchema/sessionApplicationUiSchemaController';
export { SessionApplicationUiSchemaController } from './uiSchema/sessionApplicationUiSchemaController';

export type {
  SessionSettingsControllerState,
  SessionSettingsStatusTone,
} from './sessionSettings/sessionSettingsController';
export { SessionSettingsController } from './sessionSettings/sessionSettingsController';
export type {
  ServerSettingsControllerState,
  ServerSettingsStatusTone,
} from './serverSettings/serverSettingsController';
export { ServerSettingsController } from './serverSettings/serverSettingsController';
export type { ServerSettingsInvalidationEvent } from './serverSettings/serverSettingsInvalidation';
export {
  emitServerSettingsInvalidated,
  subscribeServerSettingsInvalidated,
} from './serverSettings/serverSettingsInvalidation';

export type { SessionUiSchemaInvalidationEvent } from './uiSchema/sessionUiSchemaInvalidation';
export {
  emitSessionUiSchemaInvalidated,
  subscribeSessionUiSchemaInvalidated,
} from './uiSchema/sessionUiSchemaInvalidation';

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
  CloudConnectionRecord,
  ConnectionRecord,
} from './connections/types';

export { CONNECTIONS_STORAGE_KEY, loadConnections, saveConnections } from './connections/store';
export {
  SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
  SESSION_SCOPED_MESSAGES_CACHE_ENTRY_KEY_PREFIX,
  getSessionScopedMessagesCacheEntryKey,
  loadSessionScopedMessagesCache,
  persistSessionScopedMessagesCacheEntry,
  deleteSessionScopedMessagesCacheEntry,
  deleteConnectionSessionScopedMessagesCacheEntries,
  clearSessionScopedMessagesCache,
} from './storage/sessionScopedMessagesCache';
