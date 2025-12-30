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
  cursor_event_id?: string | null;
}

export interface SendResponse {
  status?: string;
}

export interface AgentsResponse {
  agents: string[];
}

export interface SessionAgentResponse {
  agent_id: string;
}

export interface ForkSessionResponse {
  session: { session_id: string; [key: string]: any };
  source_session_id: string;
}

export interface DeleteMessagesResponse {
  session: any;
  deleted_indices: number[];
}

export interface ListEventsParams {
  sessionId?: string;
  sinceId?: string;
  requestId?: string;
  limit?: number;
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
): Promise<ListMessagesResponse> {
  const query = buildQuery({ start, end });
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages${query}`;
  const data = (await adapter.get(path)) as ListMessagesResponse;
  const messages = Array.isArray(data.messages) ? data.messages : [];
  return {
    messages,
    cursor_event_id: data.cursor_event_id ?? null,
  };
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

// --- Event helpers ---

import type { Event } from './eventsTypes';

export async function apiListEvents(
  adapter: ConnectionAdapter,
  params: ListEventsParams = {},
): Promise<Event[]> {
  const { sessionId, sinceId, requestId, limit } = params;
  const query = buildQuery({
    session_id: sessionId,
    since_id: sinceId,
    request_id: requestId,
    // ``limit`` now applies to the compacted response size on the
    // server. Use it directly when provided so callers can bound the
    // number of events per batch, and rely on the server default
    // internal_limit for the raw event window.
    limit,
    // Always request a reasonably large internal window on the
    // server so that compaction can operate over more raw events
    // without forcing mobile to handle huge batches.
    internal_limit: 5000,
  });
  const data = (await adapter.get(`/events${query}`)) as { events?: any[] };
  const events = Array.isArray(data.events) ? data.events : [];
  return events as Event[];
}

// --- Phase 2 / advanced helpers ---

export async function apiListAgents(adapter: ConnectionAdapter): Promise<string[]> {
  const data = (await adapter.get('/agents')) as AgentsResponse;
  if (data && Array.isArray(data.agents)) {
    return data.agents;
  }
  return [];
}

export async function apiGetSessionAgent(
  adapter: ConnectionAdapter,
  sessionId: string,
): Promise<string> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/agent`;
  const data = (await adapter.get(path)) as SessionAgentResponse;
  return data.agent_id;
}

export async function apiSwitchSessionAgent(
  adapter: ConnectionAdapter,
  sessionId: string,
  agentId: string,
): Promise<void> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/agent`;
  await adapter.patch(path, { agent_id: agentId });
}

export async function apiForkSession(
  adapter: ConnectionAdapter,
  sessionId: string,
  index?: number,
): Promise<ForkSessionResponse> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/fork`;
  const payload: any = {};
  if (typeof index === 'number') {
    payload.index = index;
  }
  const data = await adapter.post(path, payload);
  return data as ForkSessionResponse;
}

export async function apiModifyMessage(
  adapter: ConnectionAdapter,
  sessionId: string,
  index: number,
  content: string,
): Promise<void> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages/${index}`;
  await adapter.patch(path, { content });
}

export async function apiDeleteMessagesByIndices(
  adapter: ConnectionAdapter,
  sessionId: string,
  indices: number[],
): Promise<DeleteMessagesResponse> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages`;
  const payload = { indices };
  const data = await adapter.delete(path, payload);
  return data as DeleteMessagesResponse;
}

export async function apiDeleteMessagesByRange(
  adapter: ConnectionAdapter,
  sessionId: string,
  start?: number,
  end?: number,
): Promise<DeleteMessagesResponse> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/messages`;
  const payload: any = { range: {} as { start?: number; end?: number } };
  if (typeof start === 'number') {
    payload.range.start = start;
  }
  if (typeof end === 'number') {
    payload.range.end = end;
  }
  const data = await adapter.delete(path, payload);
  return data as DeleteMessagesResponse;
}

// --- Session configuration helpers ---

export interface UiConfigElement {
  ui_type?: string;
  type?: string;
  key: string;
  label?: string;
  description?: string;
  plugin?: string;
  options?: any;
  [k: string]: any;
}

export interface UiElementsResponse {
  elements: UiConfigElement[];
}

export interface SessionOverridesResponse {
  overrides: Record<string, any>;
}

export async function apiGetSessionUiElements(
  adapter: ConnectionAdapter,
  sessionId: string,
): Promise<UiConfigElement[]> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/ui-elements`;
  const data = (await adapter.get(path)) as UiElementsResponse | UiConfigElement[];
  const elements = Array.isArray((data as any).elements)
    ? (data as UiElementsResponse).elements
    : (data as UiConfigElement[]);
  return Array.isArray(elements) ? elements : [];
}

export async function apiGetSessionOverrides(
  adapter: ConnectionAdapter,
  sessionId: string,
): Promise<Record<string, any>> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
  const data = (await adapter.get(path)) as SessionOverridesResponse;
  if (data && data.overrides && typeof data.overrides === 'object') {
    return data.overrides;
  }
  return {};
}

export async function apiPatchSessionOverrides(
  adapter: ConnectionAdapter,
  sessionId: string,
  values: Record<string, any>,
): Promise<void> {
  const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
  await adapter.patch(path, { values });
}
