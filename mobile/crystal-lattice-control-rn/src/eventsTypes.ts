import type { ApiMessage } from './api';

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
  | RequestCompletedEvent
  | CheckpointEvent
  | BaseEvent;
