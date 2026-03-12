import type { Transport } from '../transport/transport';
import type { Event } from '../types/events';
import type {
  ApplicationActionDefinition,
  ApplicationUiElement,
  ExecuteActionResponse,
} from '../types/plugins';
import type { IndexedMessage } from '../types/messages';
import type { SessionSummary } from '../types/sessions';
import type { ConfigSchemaEntry, UiSchemaElement } from '../types/uiSchema';
import type { SessionPluginEntry } from '../types/sessionPlugins';
import type {
  AgentBackend,
  BackendCapabilities,
  ListMessagesResult,
} from './backend';
import { generateIdempotencyKey } from '../utils/idempotency';
import { emitSessionUiSchemaInvalidated } from '../uiSchema/sessionUiSchemaInvalidation';

function buildQuery(params: Record<string, string | number | undefined>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  }
  return parts.length > 0 ? `?${parts.join('&')}` : '';
}

export class RestAgentBackend implements AgentBackend {
  readonly kind = 'rest' as const;

  private transport: Transport;

  constructor(options: { transport: Transport }) {
    this.transport = options.transport;
  }

  private buildIdempotencyHeaders(idempotencyKey?: string): Record<string, string> {
    const normalized = typeof idempotencyKey === 'string' ? idempotencyKey.trim() : '';
    return { 'Idempotency-Key': normalized || generateIdempotencyKey() };
  }

  getCapabilities(): BackendCapabilities {
    return {
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: true,
      applicationActions: true,
      applicationConfig: false,
    };
  }

  async listSessionPlugins(sessionId: string): Promise<SessionPluginEntry[]> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/plugins`;
    const resp = await this.transport.request<
      SessionPluginEntry[] | { plugins?: SessionPluginEntry[] }
    >({
      method: 'GET',
      path,
    });

    const data: any = resp.data as any;
    const plugins = Array.isArray(data?.plugins) ? data.plugins : data;
    return Array.isArray(plugins) ? (plugins as SessionPluginEntry[]) : [];
  }

  async setSessionPlugins(
    sessionId: string,
    enabled: string[],
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/plugins`;
    await this.transport.request({
      method: 'PUT',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: { enabled },
    });

    emitSessionUiSchemaInvalidated(this, sessionId, { reason: 'session_plugins_updated' });
  }

  async clearSessionPlugins(
    sessionId: string,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/plugins`;
    await this.transport.request({
      method: 'DELETE',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
    });

    emitSessionUiSchemaInvalidated(this, sessionId, { reason: 'session_plugins_updated' });
  }

  async listAgents(): Promise<string[]> {
    const resp = await this.transport.request<{ agents: string[] }>({
      method: 'GET',
      path: '/agents',
    });
    const agents = Array.isArray(resp.data?.agents) ? resp.data.agents : [];
    return agents.filter((a) => typeof a === 'string');
  }

  async createSession(params: {
    agentId?: string;
    systemMessage?: string;
    idempotencyKey?: string;
  } = {}): Promise<{
    session: { session_id: string; [key: string]: any };
  }> {
    const payload: any = {};
    if (typeof params.agentId === 'string' && params.agentId.trim()) {
      payload.agent_id = params.agentId.trim();
    }
    if (typeof params.systemMessage === 'string' && params.systemMessage.trim()) {
      payload.system_message = params.systemMessage.trim();
    }
    const resp = await this.transport.request({
      method: 'POST',
      path: '/sessions',
      headers: this.buildIdempotencyHeaders(params.idempotencyKey),
      body: payload,
    });
    return resp.data as any;
  }

  async listSessions(params: { limit?: number } = {}): Promise<SessionSummary[]> {
    const query = buildQuery({ limit: params.limit });
    const resp = await this.transport.request<{ sessions: SessionSummary[] }>({
      method: 'GET',
      path: `/sessions${query}`,
    });
    const sessions = Array.isArray(resp.data?.sessions) ? resp.data.sessions : [];
    return sessions;
  }

  async listMessages(
    sessionId: string,
    params: { start?: number; end?: number } = {},
  ): Promise<ListMessagesResult> {
    const query = buildQuery({ start: params.start, end: params.end });
    const path = `/sessions/${encodeURIComponent(sessionId)}/messages${query}`;
    const resp = await this.transport.request<{
      messages: IndexedMessage[];
      cursor_event_id?: string | null;
      active_request_id?: string | null;
    }>({ method: 'GET', path });

    const messages = Array.isArray(resp.data?.messages) ? resp.data.messages : [];

    return {
      messages,
      cursorEventId: resp.data?.cursor_event_id ?? null,
      activeRequestId: resp.data?.active_request_id ?? null,
    };
  }

  async appendMessage(
    sessionId: string,
    message: {
      role: 'user' | 'assistant' | 'system' | 'tool';
      content: string;
      multipartContent?: any[] | null;
      metadata?: Record<string, any>;
    },
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/messages`;
    const payload: any = { role: message.role, content: message.content };
    if (message.multipartContent !== undefined) {
      payload.multipartContent = message.multipartContent;
    }
    if (message.metadata && Object.keys(message.metadata).length > 0) {
      payload.metadata = message.metadata;
    }
    await this.transport.request({
      method: 'POST',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: payload,
    });
  }

  async sendMessage(
    sessionId: string,
    params: {
      message: {
        role: 'user' | 'assistant' | 'system' | 'tool';
        content: string;
        multipartContent?: any[] | null;
        metadata?: Record<string, any>;
      };
      configOverrides?: Record<string, any>;
      idempotencyKey?: string;
    },
  ): Promise<{ status?: string; request_id?: string; session_id?: string }> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/send_message`;
    const message: any = {
      role: params.message.role,
      content: params.message.content,
    };
    if (params.message.multipartContent !== undefined) {
      message.multipartContent = params.message.multipartContent;
    }
    if (params.message.metadata && Object.keys(params.message.metadata).length > 0) {
      message.metadata = params.message.metadata;
    }

    const payload = {
      message,
      config_overrides: params.configOverrides ?? {},
    };

    const resp = await this.transport.request({
      method: 'POST',
      path,
      headers: this.buildIdempotencyHeaders(params.idempotencyKey),
      body: payload,
    });
    return resp.data as any;
  }

  async send(
    sessionId: string,
    params: { configOverrides?: Record<string, any>; idempotencyKey?: string } = {},
  ): Promise<{ status?: string; request_id?: string }> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/send`;
    const payload = { config_overrides: params.configOverrides || {} };
    const resp = await this.transport.request({
      method: 'POST',
      path,
      headers: this.buildIdempotencyHeaders(params.idempotencyKey),
      body: payload,
    });
    return resp.data as any;
  }

  async cancelRequest(
    requestId: string,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/requests/${encodeURIComponent(requestId)}/cancel`;
    await this.transport.request({
      method: 'POST',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: {},
    });
  }

  async listEvents(params: {
    sessionId: string;
    sinceId?: string;
    requestId?: string;
    limit?: number;
  }): Promise<Event[]> {
    const query = buildQuery({
      session_id: params.sessionId,
      since_id: params.sinceId,
      request_id: params.requestId,
      limit: params.limit,
      internal_limit: 5000,
    });

    const resp = await this.transport.request<{ events?: any[] }>({
      method: 'GET',
      path: `/events${query}`,
    });
    const events = Array.isArray(resp.data?.events) ? resp.data.events : [];
    return events as Event[];
  }

  async getSessionAgent(sessionId: string): Promise<string> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/agent`;
    const resp = await this.transport.request<{ agent_id: string }>({
      method: 'GET',
      path,
    });
    return resp.data?.agent_id;
  }

  async switchSessionAgent(
    sessionId: string,
    agentId: string,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/agent`;
    await this.transport.request({
      method: 'PATCH',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: { agent_id: agentId },
    });
  }

  async forkSession(
    sessionId: string,
    params: { index?: number; idempotencyKey?: string } = {},
  ): Promise<{ session: { session_id: string; [key: string]: any }; source_session_id: string }> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/fork`;
    const payload: any = {};
    if (typeof params.index === 'number') {
      payload.index = params.index;
    }
    const resp = await this.transport.request({
      method: 'POST',
      path,
      headers: this.buildIdempotencyHeaders(params.idempotencyKey),
      body: payload,
    });
    return resp.data as any;
  }

  async modifyMessage(
    sessionId: string,
    index: number,
    content: string,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/messages/${index}`;
    await this.transport.request({
      method: 'PATCH',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: { content },
    });
  }

  async deleteMessages(
    sessionId: string,
    params: { indices?: number[]; range?: { start?: number; end?: number } },
    options: { idempotencyKey?: string } = {},
  ): Promise<{ deleted_indices?: number[]; session?: any }> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/messages`;
    const payload: any = {};
    if (Array.isArray(params.indices)) {
      payload.indices = params.indices;
    }
    if (params.range && typeof params.range === 'object') {
      payload.range = {};
      if (typeof params.range.start === 'number') payload.range.start = params.range.start;
      if (typeof params.range.end === 'number') payload.range.end = params.range.end;
    }

    const resp = await this.transport.request({
      method: 'DELETE',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: payload,
    });
    return resp.data as any;
  }

  async getSessionUiSchema(sessionId: string): Promise<UiSchemaElement[]> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/ui-schema`;
    const resp = await this.transport.request<UiSchemaElement[] | { elements?: UiSchemaElement[] }>({
      method: 'GET',
      path,
    });

    const data: any = resp.data as any;
    const elements = Array.isArray(data?.elements) ? data.elements : data;
    return Array.isArray(elements) ? elements : [];
  }

  async getSessionOverrides(sessionId: string): Promise<Record<string, any>> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
    const resp = await this.transport.request<{ overrides?: Record<string, any> }>({
      method: 'GET',
      path,
    });
    if (resp.data && resp.data.overrides && typeof resp.data.overrides === 'object') {
      return resp.data.overrides;
    }
    return {};
  }

  async patchSessionOverrides(
    sessionId: string,
    values: Record<string, any>,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
    await this.transport.request({
      method: 'PATCH',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
      body: { values },
    });

    emitSessionUiSchemaInvalidated(this, sessionId, { reason: 'session_overrides_updated' });
  }

  async deleteSessionOverride(
    sessionId: string,
    key: string,
    options: { idempotencyKey?: string } = {},
  ): Promise<void> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/overrides/${encodeURIComponent(key)}`;
    await this.transport.request({
      method: 'DELETE',
      path,
      headers: this.buildIdempotencyHeaders(options.idempotencyKey),
    });

    emitSessionUiSchemaInvalidated(this, sessionId, { reason: 'session_overrides_updated' });
  }

  async getSessionConfigSchema(sessionId: string): Promise<ConfigSchemaEntry[]> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/config/schema`;
    const resp = await this.transport.request<ConfigSchemaEntry[] | { schema?: ConfigSchemaEntry[] }>({
      method: 'GET',
      path,
    });
    const data: any = resp.data as any;
    const schema = Array.isArray(data?.schema) ? data.schema : data;
    return Array.isArray(schema) ? schema : [];
  }

  async getSessionBaseConfig(sessionId: string): Promise<Record<string, any>> {
    const path = `/sessions/${encodeURIComponent(sessionId)}/config/base`;
    const resp = await this.transport.request<{ config?: Record<string, any> }>({
      method: 'GET',
      path,
    });
    if (resp.data && resp.data.config && typeof resp.data.config === 'object') {
      return resp.data.config;
    }
    return {};
  }

  async listApplicationActions(params: { pluginId?: string } = {}): Promise<ApplicationActionDefinition[]> {
    const query = buildQuery({ plugin: params.pluginId });
    const resp = await this.transport.request<{ actions?: ApplicationActionDefinition[] }>({
      method: 'GET',
      path: `/application/actions${query}`,
    });
    const actions = Array.isArray(resp.data?.actions) ? resp.data.actions : [];
    return actions;
  }

  async listApplicationUiSchema(params: { pluginId?: string } = {}): Promise<ApplicationUiElement[]> {
    const query = buildQuery({ plugin: params.pluginId });
    const resp = await this.transport.request<{ elements?: ApplicationUiElement[] }>({
      method: 'GET',
      path: `/application/ui-schema${query}`,
    });
    const elements = Array.isArray(resp.data?.elements) ? resp.data.elements : [];
    return elements;
  }

  async executeAction(params: {
    pluginId: string;
    actionId: string;
    actionOwner?: string;
    inputs: Record<string, any>;
    idempotencyKey?: string;
  }): Promise<ExecuteActionResponse> {
    const payload = {
      plugin: params.pluginId,
      action_id: params.actionId,
      action_owner: params.actionOwner,
      inputs: params.inputs,
    };
    const resp = await this.transport.request<ExecuteActionResponse>({
      method: 'POST',
      path: '/actions',
      headers: this.buildIdempotencyHeaders(params.idempotencyKey),
      body: payload,
    });
    return resp.data;
  }
}
