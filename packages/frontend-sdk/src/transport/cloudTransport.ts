import type {
  HttpMethod,
  PathPrefixTimeoutRule,
  Transport,
  TransportTimeoutRule,
} from './transport';
import { resolveTransportTimeoutMs } from './transport';

export interface CloudConnectionLink {
  orchestratorUrl: string;
  connectionId?: string;
  instanceId?: string;
  sessionId?: string;
  token: string;
}

export function parseCloudConnectionLink(raw: string): CloudConnectionLink {
  const prefix = 'crystal-lattice-cloud://connect?';
  if (!raw.startsWith(prefix)) {
    throw new Error('Unsupported cloud connection link protocol');
  }
  const params = parseQuery(raw.slice(prefix.length));
  const orchestratorUrl = params.orchestrator || '';
  const connectionId = params.connection_id || '';
  const instanceId = params.instance_id || '';
  const sessionId = params.session_id || '';
  const token = params.token || '';

  if (!orchestratorUrl || (!connectionId && !instanceId) || !token) {
    throw new Error('Cloud connection link is missing required fields');
  }

  return {
    orchestratorUrl,
    ...(connectionId ? { connectionId } : {}),
    ...(instanceId ? { instanceId } : {}),
    ...(sessionId ? { sessionId } : {}),
    token,
  };
}

export function formatCloudConnectionLink(link: CloudConnectionLink): string {
  const values: Record<string, string> = {
    orchestrator: link.orchestratorUrl,
    token: link.token,
  };
  if (link.connectionId) values.connection_id = link.connectionId;
  if (link.instanceId) values.instance_id = link.instanceId;
  if (link.sessionId) values.session_id = link.sessionId;
  return `crystal-lattice-cloud://connect?${formatQuery(values)}`;
}

function parseQuery(query: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of query.split('&')) {
    if (!part) continue;
    const eq = part.indexOf('=');
    const rawKey = eq >= 0 ? part.slice(0, eq) : part;
    const rawValue = eq >= 0 ? part.slice(eq + 1) : '';
    const key = decodeURIComponent(rawKey.replace(/\+/g, ' '));
    out[key] = decodeURIComponent(rawValue.replace(/\+/g, ' '));
  }
  return out;
}

function formatQuery(values: Record<string, string>): string {
  return Object.entries(values)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
}

export class CloudTransport implements Transport {
  private readonly orchestratorUrl: string;
  private readonly connectionId?: string;
  private readonly instanceId?: string;
  private readonly token: string;
  private readonly fetchImpl: typeof fetch;
  private readonly defaultRequestTimeoutMs?: number;
  private readonly timeoutRules: TransportTimeoutRule[];
  private readonly timeoutMsByPathPrefix: PathPrefixTimeoutRule[];

  constructor(options: {
    orchestratorUrl: string;
    connectionId?: string;
    instanceId?: string;
    token: string;
    fetchImpl?: typeof fetch;
    defaultRequestTimeoutMs?: number;
    timeoutRules?: TransportTimeoutRule[];
    timeoutMsByPathPrefix?: PathPrefixTimeoutRule[];
  }) {
    this.orchestratorUrl = options.orchestratorUrl.replace(/\/$/, '');
    this.connectionId = options.connectionId;
    this.instanceId = options.instanceId;
    this.token = options.token;
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.defaultRequestTimeoutMs = options.defaultRequestTimeoutMs;
    this.timeoutRules = options.timeoutRules ?? [];
    this.timeoutMsByPathPrefix = options.timeoutMsByPathPrefix ?? [];
    if (!this.connectionId && !this.instanceId) {
      throw new Error('CloudTransport requires connectionId or instanceId');
    }
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    const proxiedPath = req.path.startsWith('/') ? req.path.slice(1) : req.path;
    const proxyPrefix = this.connectionId
      ? `/connections/${encodeURIComponent(this.connectionId)}/proxy`
      : `/instances/${encodeURIComponent(this.instanceId || '')}/proxy`;
    const url = `${this.orchestratorUrl}${proxyPrefix}/${proxiedPath}`;
    const timeoutMs = resolveTransportTimeoutMs({
      method: req.method,
      path: req.path,
      timeoutMs: req.timeoutMs,
      defaultRequestTimeoutMs: this.defaultRequestTimeoutMs,
      timeoutRules: this.timeoutRules,
      timeoutMsByPathPrefix: this.timeoutMsByPathPrefix,
    });

    const headers: Record<string, string> = {
      ...(req.headers || {}),
      authorization: `Bearer ${this.token}`,
    };
    let body: any = undefined;
    if (req.body !== undefined) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
      body = JSON.stringify(req.body);
    }

    const controller = typeof AbortController === 'function' ? new AbortController() : null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let didTimeout = false;
    if (controller && typeof timeoutMs === 'number') {
      timeoutId = setTimeout(() => {
        didTimeout = true;
        controller.abort();
      }, timeoutMs);
    }

    let resp: Response;
    try {
      resp = await this.fetchImpl(url, {
        method: req.method,
        headers,
        body,
        signal: controller?.signal,
      });
    } catch (err) {
      if (timeoutId) clearTimeout(timeoutId);
      if (didTimeout) {
        throw new Error(`Request timeout after ${timeoutMs}ms (cloud ${req.method} ${req.path})`);
      }
      throw err;
    }
    if (timeoutId) clearTimeout(timeoutId);

    const text = await resp.text();
    let data: any = text;
    const contentType = resp.headers.get('content-type') || '';
    if (text && contentType.includes('application/json')) {
      data = JSON.parse(text);
    }
    return { status: resp.status, data };
  }
}