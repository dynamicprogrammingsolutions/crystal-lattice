import type { ApiMessage } from './messages';
import type { SessionSummary } from './sessions';

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export interface JsonProjectionOptions {
  include?: readonly string[];
  exclude?: readonly string[];
}

export interface SessionDataQueryParams extends JsonProjectionOptions {
  filters?: Readonly<Record<string, unknown>>;
  applyFilterDefaults?: boolean;
  limit?: number;
}

export interface MessageDataQueryParams extends JsonProjectionOptions {
  start?: number;
  end?: number;
}

export type ProjectedSessionSummary = Partial<SessionSummary> & {
  [key: string]: unknown;
};

export type ProjectedApiMessage = Partial<ApiMessage> & {
  [key: string]: unknown;
};

export interface ProjectedIndexedMessage {
  index?: number;
  message?: ProjectedApiMessage;
  [key: string]: unknown;
}

export interface ProjectedSessionQueryDocument {
  sessions?: ProjectedSessionSummary[];
  [key: string]: unknown;
}

export interface ProjectedMessageQueryDocument {
  messages?: ProjectedIndexedMessage[];
  cursor_event_id?: string | null;
  active_request_id?: string | null;
  readonly?: boolean;
  snapshot_id?: string | null;
  [key: string]: unknown;
}

export type SessionDataQueryResult = ProjectedSessionQueryDocument | null;
export type MessageDataQueryResult = ProjectedMessageQueryDocument | null;