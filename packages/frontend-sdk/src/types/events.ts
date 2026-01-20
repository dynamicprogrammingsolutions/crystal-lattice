import type { ApiMessage } from './messages';

export interface BaseEvent {
  event_id: string;
  type: string;
  session_id: string;
  request_id?: string;
  // Allow additional properties for forward compatibility.
  [key: string]: any;
}

export interface FinalEvent extends BaseEvent {
  type: 'final';
  messages: ApiMessage[];
}

export interface MessageAppendedEvent extends BaseEvent {
  type: 'message_appended';
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  metadata?: Record<string, any> | null;
  message?: ApiMessage;
}

export interface ToolResultsEvent extends BaseEvent {
  type: 'tool_results';
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
  | FinalEvent
  | MessageAppendedEvent
  | ToolResultsEvent
  | RequestStartedEvent
  | ErrorEvent
  | AssistantMessageEvent
  | PartialEvent
  | RequestCompletedEvent
  | CheckpointEvent
  | BaseEvent;
