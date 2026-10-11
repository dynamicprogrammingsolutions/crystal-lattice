import type { BridgeServer } from './bridgeTransport';
import type { BridgeConnectionTransportOptions } from './bridgeConnectionTransport';
import type { HttpMethod, TransportTimeoutRule } from './transport';
import { resolveTransportTimeoutMs } from './transport';

function generateUuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
    // eslint-disable-next-line no-bitwise
    const random = (Math.random() * 16) | 0;
    // eslint-disable-next-line no-bitwise
    const value = character === 'x' ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export function deriveBridgeHttpBaseUrl(bridgeUrl: string): string {
  // React Native's ambient URL declaration is intentionally minimal even
  // though its runtime implementation exposes the standard mutable fields.
  const parsed = new URL(bridgeUrl) as unknown as {
    protocol: string;
    pathname: string;
    search: string;
    hash: string;
    toString(): string;
  };
  if (parsed.protocol === 'ws:') {
    parsed.protocol = 'http:';
  } else if (parsed.protocol === 'wss:') {
    parsed.protocol = 'https:';
  } else if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error(`Unsupported bridge URL scheme: ${parsed.protocol}`);
  }

  const normalizedPath = parsed.pathname.replace(/\/+$/, '');
  if (normalizedPath.endsWith('/ws/websocket')) {
    parsed.pathname = normalizedPath.slice(0, -'/ws/websocket'.length) || '/';
  } else if (normalizedPath.endsWith('/ws')) {
    parsed.pathname = normalizedPath.slice(0, -'/ws'.length) || '/';
  }
  parsed.search = '';
  parsed.hash = '';
  return parsed.toString().replace(/\/$/, '');
}

function isBinaryBody(value: any): boolean {
  if (typeof ArrayBuffer !== 'undefined' && value instanceof ArrayBuffer) {
    return true;
  }
  if (typeof ArrayBuffer !== 'undefined' && ArrayBuffer.isView(value)) {
    return true;
  }
  const BlobType = (globalThis as any).Blob;
  return typeof BlobType === 'function' && value instanceof BlobType;
}

function isTextContentType(contentType: string): boolean {
  return (
    contentType.startsWith('text/') ||
    contentType.includes('xml') ||
    contentType.includes('javascript') ||
    contentType.includes('x-www-form-urlencoded')
  );
}

export class HttpBridgeTransport {
  private readonly bridgeHttpBaseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly clientId: string;
  private readonly defaultRequestTimeoutMs?: number;
  private readonly timeoutRules: TransportTimeoutRule[];
  private readonly timeoutMsByPathPrefix: BridgeConnectionTransportOptions['timeoutMsByPathPrefix'];
  private readonly activeControllers = new Set<AbortController>();

  private serverId: string | null;
  private pairingToken: string | null;
  private pairingRequestToken: string | null = null;
  private forceValidateBeforeNextRequest = false;

  constructor(options: BridgeConnectionTransportOptions) {
    this.bridgeHttpBaseUrl = (
      options.bridgeHttpBaseUrl ?? deriveBridgeHttpBaseUrl(options.bridgeUrl)
    ).replace(/\/$/, '');
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.clientId = options.clientId ?? generateUuid();
    this.serverId = options.serverId ?? null;
    this.pairingToken = options.pairingToken ?? null;
    this.defaultRequestTimeoutMs = options.defaultRequestTimeoutMs;
    this.timeoutRules = options.timeoutRules ?? [];
    this.timeoutMsByPathPrefix = options.timeoutMsByPathPrefix ?? [];
  }

  getPairingToken(): string | null {
    return this.pairingToken;
  }

  getServerId(): string | null {
    return this.serverId;
  }

  isPaired(): boolean {
    return !!this.pairingToken && !!this.serverId;
  }

  async connect(): Promise<void> {
    let capability: { protocol_version?: number };
    try {
      capability = await this.controlRequest({
        method: 'GET',
        path: '/bridge/v1/capabilities',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (message.includes('HTTP 404 ') || message.includes('HTTP 405 ')) {
        throw new Error('Bridge does not support HTTP transport protocol v1');
      }
      throw error;
    }
    if (capability?.protocol_version !== 1) {
      throw new Error('Bridge does not support HTTP transport protocol v1');
    }

    if (this.pairingToken && this.serverId) {
      await this.resumePairing();
    }
    this.forceValidateBeforeNextRequest = false;
  }

  disconnect(): void {
    for (const controller of this.activeControllers) {
      controller.abort();
    }
    this.activeControllers.clear();
  }

  prepareForResume(): void {
    this.forceValidateBeforeNextRequest = true;
  }

  async listServers(): Promise<BridgeServer[]> {
    const data = await this.controlRequest<{ servers?: BridgeServer[] }>({
      method: 'GET',
      path: '/bridge/v1/servers',
    });
    return Array.isArray(data?.servers) ? data.servers : [];
  }

  async requestPairing(serverId: string): Promise<void> {
    const data = await this.controlRequest<{ pairing_request_token?: string }>({
      method: 'POST',
      path: '/bridge/v1/pairings/request',
      body: { server_id: serverId, client_id: this.clientId },
    });
    if (!data?.pairing_request_token) {
      throw new Error('Bridge pairing response did not include a request token');
    }
    this.serverId = serverId;
    this.pairingRequestToken = data.pairing_request_token;
  }

  async submitPairingCode(serverId: string, code: string): Promise<void> {
    if (!this.pairingRequestToken || this.serverId !== serverId) {
      throw new Error('No pending HTTP bridge pairing request');
    }
    const data = await this.controlRequest<{
      server_id?: string;
      pairing_token?: string;
    }>({
      method: 'POST',
      path: '/bridge/v1/pairings/confirm',
      body: {
        pairing_request_token: this.pairingRequestToken,
        code,
      },
    });
    if (!data?.pairing_token || data.server_id !== serverId) {
      throw new Error('Bridge pairing response was incomplete');
    }
    this.serverId = serverId;
    this.pairingToken = data.pairing_token;
    this.pairingRequestToken = null;
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
    signal?: AbortSignal;
  }): Promise<{ status: number; data: T }> {
    if (!this.pairingToken || !this.serverId) {
      throw new Error('Not paired with any server');
    }
    if (this.forceValidateBeforeNextRequest) {
      await this.resumePairing();
      this.forceValidateBeforeNextRequest = false;
    }

    const timeoutMs = resolveTransportTimeoutMs({
      method: req.method,
      path: req.path,
      timeoutMs: req.timeoutMs,
      defaultRequestTimeoutMs: this.defaultRequestTimeoutMs,
      timeoutRules: this.timeoutRules,
      timeoutMsByPathPrefix: this.timeoutMsByPathPrefix,
    });
    const headers: Record<string, string> = {
      ...(req.headers ?? {}),
      'X-Crystal-Bridge-Token': this.pairingToken,
    };
    let body: any = undefined;
    if (req.body !== undefined) {
      headers['X-Crystal-Bridge-Body-Present'] = '1';
      if (isBinaryBody(req.body)) {
        body = req.body;
      } else {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
        body = JSON.stringify(req.body);
      }
    }

    const proxiedPath = req.path.startsWith('/') ? req.path.slice(1) : req.path;
    const response = await this.fetchWithTimeout(
      `${this.bridgeHttpBaseUrl}/bridge/v1/proxy/${proxiedPath}`,
      {
        method: req.method,
        headers,
        body,
      },
      timeoutMs,
      `HTTP ${req.method} ${req.path}`,
      req.signal,
    );
    return await this.parseResponse<T>(response, req.method, req.path);
  }

  private async resumePairing(): Promise<void> {
    if (!this.pairingToken || !this.serverId) {
      return;
    }
    await this.controlRequest({
      method: 'POST',
      path: '/bridge/v1/pairings/resume',
      token: this.pairingToken,
      body: { server_id: this.serverId },
    });
  }

  private async controlRequest<T>(options: {
    method: 'GET' | 'POST';
    path: string;
    token?: string;
    body?: any;
  }): Promise<T> {
    const headers: Record<string, string> = {};
    let body: string | undefined;
    if (options.token) {
      headers['X-Crystal-Bridge-Token'] = options.token;
    }
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(options.body);
    }
    const response = await this.fetchWithTimeout(
      `${this.bridgeHttpBaseUrl}${options.path}`,
      { method: options.method, headers, body },
      this.defaultRequestTimeoutMs,
      `${options.method} ${options.path}`,
    );
    const parsed = await this.parseResponse<T>(
      response,
      options.method as HttpMethod,
      options.path,
    );
    return parsed.data;
  }

  private async fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number | undefined,
    context: string,
    externalSignal?: AbortSignal,
  ): Promise<Response> {
    const controller = typeof AbortController === 'function' ? new AbortController() : null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let didTimeout = false;
    const abortFromExternal = () => controller?.abort();
    if (controller) {
      this.activeControllers.add(controller);
      init.signal = controller.signal;
      if (externalSignal?.aborted) {
        controller.abort();
      } else {
        externalSignal?.addEventListener('abort', abortFromExternal);
      }
      if (typeof timeoutMs === 'number') {
        timeoutId = setTimeout(() => {
          didTimeout = true;
          controller.abort();
        }, timeoutMs);
      }
    }

    try {
      return await this.fetchImpl(url, init);
    } catch (error) {
      if (didTimeout) {
        throw new Error(`Request timeout after ${timeoutMs}ms (${context})`);
      }
      throw error;
    } finally {
      externalSignal?.removeEventListener('abort', abortFromExternal);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (controller) {
        this.activeControllers.delete(controller);
      }
    }
  }

  private async parseResponse<T>(
    response: Response,
    method: HttpMethod,
    path: string,
  ): Promise<{ status: number; data: T }> {
    const contentType = response.headers.get('content-type') || '';
    let data: any;
    if (contentType.includes('application/json')) {
      const text = await response.text();
      data = text ? JSON.parse(text) : null;
    } else if (isTextContentType(contentType)) {
      data = await response.text();
    } else {
      data = await response.arrayBuffer();
    }

    if (!response.ok) {
      const detail =
        typeof data === 'string'
          ? data
          : data && typeof data === 'object' && 'error' in data
          ? (data as any).error
          : JSON.stringify(data);
      throw new Error(`HTTP ${response.status} ${method} ${path}: ${detail}`);
    }
    return { status: response.status, data: data as T };
  }
}
