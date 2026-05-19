export type MessageRole = 'system' | 'user' | 'assistant' | 'tool' | (string & {});

export interface ApiMessage {
  role: MessageRole;
  content: string;
  multipartContent?: any[] | null;
  toolResult?: Record<string, any> | null;
  metadata?: Record<string, any> | null;
}

export interface IndexedMessage {
  index: number;
  message: ApiMessage;
}
