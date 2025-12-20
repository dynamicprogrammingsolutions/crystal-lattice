import type { ConnectionAdapter } from '../App';

export interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
}

export interface ApiMessage {
  role: string;
  content: string;
  metadata?: Record<string, any> | null;
}

export interface IndexedMessage {
  index: number;
  message: ApiMessage;
}

export interface CreateSessionResponse {
  session: { session_id: string; [key: string]: any };
}

export interface ListSessionsResponse {
  sessions: SessionSummary[];
}

export interface ListMessagesResponse {
  messages: IndexedMessage[];
}

export interface SendResponse {
  session: any;
  messages: ApiMessage[];
  request_id?: string | null;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  }
  return parts.length > 0 ? `?${parts.join('&')}` : '';
}

export async function apiCreateSession(
  adapter: ConnectionAdapter,
  agentId: string = 'default',
  systemMessage?: string,
): Promise<CreateSessionResponse> {
  const payload: any = { agent_id: agentId };
  if (typeof systemMessage === 'string' && systemMessage.trim()) {
    payload.system_message = systemMessage.trim();
  }
  const data = await adapter.post('/sessions', payload);
  return data as CreateSessionResponse;
}

export async function apiListSessions(
  adapter: ConnectionAdapter,
  limit?: number,
): Promise<SessionSummary[]> {
  const query = buildQuery({ limit: limit !== undefined ? limit : undefined });
  const data = (await adapter.get(`/sessions${query}`)) as ListSessionsResponse;
  return Array.isArray(data.sessions) ? data.sessions : [];
}

export async function apiListMessages(
  adapter: ConnectionAdapter,
  sessionId: string,
  start?: number,
  end?: number,
): Promise<IndexedMessage[]> {
  const query = buildQuery({ start, end });
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages${query}`;
  const data = (await adapter.get(path)) as ListMessagesResponse;
  return Array.isArray(data.messages) ? data.messages : [];
}

export async function apiAppendMessage(
  adapter: ConnectionAdapter,
  sessionId: string,
  role: 'user' | 'assistant' | 'system' | 'tool',
  content: string,
  metadata?: Record<string, any>,
): Promise<void> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages`;
  const payload: any = { role, content };
  if (metadata && Object.keys(metadata).length > 0) {
    payload.metadata = metadata;
  }
  await adapter.post(path, payload);
}

export async function apiSend(
  adapter: ConnectionAdapter,
  sessionId: string,
): Promise<SendResponse> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/send`;
  // Config overrides are handled on the server side for now.
  const payload = { config_overrides: {} };
  const data = await adapter.post(path, payload);
  return data as SendResponse;
}
