// This module is intentionally "types only".
//
// The mobile app calls the backend via `AgentBackend` now (Phase 2+).
// These exports exist to keep local imports stable.

export type {
  ApiMessage,
  IndexedMessage,
  SessionSummary,
  UiSchemaElement,
  ConfigSchemaEntry,
  ActionInputParam,
  ApplicationActionDefinition,
  ApplicationActionUiElement,
  ApplicationNotification,
  ActionUiElement,
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
  SessionListFieldElement,
  ApplicationUiElement,
  ExecuteActionResponse,
  ExecuteActionResponseOk,
  ExecuteActionResponseError,
} from '@crystal-lattice/frontend-sdk';
