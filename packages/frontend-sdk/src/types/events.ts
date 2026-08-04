import type { ApiMessage } from './messages';
import type { ApplicationNotificationEvent } from './applicationNotifications';
import type { SessionNotificationEvent } from './notifications';

export interface BaseEvent {
  event_id: string;
  type: string;
  session_id: string;
  request_id?: string;
  // Allow additional properties for forward compatibility.
  [key: string]: any;
}

export interface SessionCreatedEvent extends BaseEvent {
  type: 'session_created';
  agent_id?: string;
  source_session_id?: string;
  fork_upto_index?: number;
}

export interface FinalEvent extends BaseEvent {
  type: 'final';
  start_index: number;
  messages: ApiMessage[];
}

export interface MessageAppendedEvent extends BaseEvent {
  type: 'message_appended';
  index: number;
  message: ApiMessage;
  role?: 'user' | 'assistant' | 'system' | 'tool';
  content?: string;
  metadata?: Record<string, any> | null;
}

export interface MessageModifiedEvent extends BaseEvent {
  type: 'message_modified';
  index: number;
  message: ApiMessage;
  content?: string;
}

export interface MessagesDeletedEvent extends BaseEvent {
  type: 'messages_deleted';
  indices: number[];
}

export interface ToolResultsEvent extends BaseEvent {
  type: 'tool_results';
  start_index: number;
  messages: ApiMessage[];
}

export interface RequestCompletedEvent extends BaseEvent {
  type: 'request_completed';
}

export interface RequestStartedEvent extends BaseEvent {
  type: 'request_started';
  stream?: boolean;
}

export interface ErrorEvent extends BaseEvent {
  type: 'error';
  detail?: string;
}

export interface AssistantMessageEvent extends BaseEvent {
  type: 'assistant_message';
  phase: 'start' | 'end';
}

export interface PartialEvent extends BaseEvent {
  type: 'partial';
  message: ApiMessage;
}

export interface CheckpointEvent extends BaseEvent {
  type: 'checkpoint';
  timestamp?: string;
}

export type Event =
  | SessionCreatedEvent
  | FinalEvent
  | MessageAppendedEvent
  | MessageModifiedEvent
  | MessagesDeletedEvent
  | ToolResultsEvent
  | RequestStartedEvent
  | ErrorEvent
  | AssistantMessageEvent
  | PartialEvent
  | RequestCompletedEvent
  | CheckpointEvent
  | ApplicationNotificationEvent
  | SessionNotificationEvent
  | BaseEvent;
