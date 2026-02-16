import type { HttpMethod, Transport } from './transport';

export interface BridgeServer {
  server_id: string;
  display_name: string;
  computer_name: string;
  location?: string;
}

export interface WebSocketLike {
  readonly readyState: number;
  onopen: ((ev?: any) => void) | null;
  onmessage: ((ev: { data: string }) => void) | null;
  onerror: ((ev: any) => void) | null;
  onclose: ((ev: { code?: number; reason?: string; wasClean?: boolean }) => void) | null;
  send(data: string): void;
  close(code?: number, reason?: string): void;
}

export type WebSocketFactory = (url: string) => WebSocketLike;

function generateUuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    // eslint-disable-next-line no-bitwise
    const r = (Math.random() * 16) | 0;
    // eslint-disable-next-line no-bitwise
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export class BridgeTransport implements Transport {
  private bridgeUrl: string;
  private wsFactory: WebSocketFactory;
  private ws: WebSocketLike | null = null;
  private clientId: string;
  private refCounter = 0;
  private connectPromise: Promise<void> | null = null;

  private readonly chunkingThresholdBytes: number;
  private readonly chunkSizeBytes: number;
  private readonly defaultRequestTimeoutMs: number;
  private readonly debug: boolean;
  private readonly logger: (msg: string, meta?: any) => void;
  private readonly timeoutMsByPathPrefix: Array<{ pathPrefix: string; timeoutMs: number }>;

  private responseHandlers: Map<string, (data: any) => void> = new Map();
  private streamingResponses: Map<
    string,
    {
      status: number | null;
      headers: Record<string, string> | null;
      chunks: string[];
      resolve: (resp: { status: number; headers: Record<string, string>; body: string }) => void;
      reject: (err: any) => void;
      timeoutId: any;
    }
  > = new Map();

  private serverId: string | null = null;
  private pairingToken: string | null = null;
  private sessionId: string | null = null;

  constructor(options: {
    bridgeUrl: string;
    serverId?: string | null;
    pairingToken?: string | null;
    wsFactory?: WebSocketFactory;
    clientId?: string;
    chunkingThresholdBytes?: number;
    chunkSizeBytes?: number;
    defaultRequestTimeoutMs?: number;
    debug?: boolean;
    logger?: (msg: string, meta?: any) => void;
    timeoutMsByPathPrefix?: Array<{ pathPrefix: string; timeoutMs: number }>;
  }) {
    this.bridgeUrl = options.bridgeUrl;
    this.serverId = options.serverId ?? null;
    this.pairingToken = options.pairingToken ?? null;
    this.clientId = options.clientId ?? generateUuid();

    this.chunkingThresholdBytes = options.chunkingThresholdBytes ?? 256 * 1024;
    // Keep a safe headroom so the Phoenix envelope stays < ~1MiB.
    this.chunkSizeBytes = options.chunkSizeBytes ?? 900 * 1024;
    this.defaultRequestTimeoutMs = options.defaultRequestTimeoutMs ?? 120_000;
    this.debug = options.debug ?? false;
    this.logger = options.logger ?? ((msg: string, meta?: any) => console.log(msg, meta ?? ''));
    this.timeoutMsByPathPrefix = options.timeoutMsByPathPrefix ?? [];

    this.wsFactory =
      options.wsFactory ??
      ((url: string) => {
        const WS = (globalThis as any).WebSocket as undefined | (new (u: string) => WebSocketLike);
        if (!WS) {
          throw new Error('No WebSocket implementation available');
        }
        return new WS(url);
      });
  }

  getPairingToken(): string | null {
    return this.pairingToken;
  }

  getServerId(): string | null {
    return this.serverId;
  }

  isPaired(): boolean {
    return !!this.sessionId;
  }

  async connect(): Promise<void> {
    await this.ensureConnected();
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    await this.ensureConnected();

    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = generateUuid();
    const headers = req.headers || {};
    const body = req.body === undefined ? null : JSON.stringify(req.body);

    const bodySizeBytes = body === null ? 0 : this.utf8ByteLength(body);
    const willChunkRequestBody = body !== null && bodySizeBytes > this.chunkingThresholdBytes;

    const timeoutMs =
      req.timeoutMs ??
      this.resolveTimeoutMsForPath(req.path) ??
      this.defaultRequestTimeoutMs;
    const responsePromise = this.createStreamingResponsePromise(requestId, timeoutMs, {
      method: req.method,
      path: req.path,
    });

    if (this.debug) {
      this.logger('[bridge] request:start', {
        requestId,
        method: req.method,
        path: req.path,
        timeoutMs,
        bodySizeBytes,
        willChunkRequestBody,
        chunkSizeBytes: this.chunkSizeBytes,
      });
    }

    try {
      let reply: any;
      if (willChunkRequestBody) {
        if (this.debug) {
          this.logger('[bridge] request:chunked:init_send', { requestId });
        }
        await this.sendMessage(
          `app:${this.clientId}`,
          'http_request_init',
          {
            request_id: requestId,
            session_id: this.sessionId,
            method: req.method,
            path: req.path,
            headers,
            body_encoding: 'utf8-json',
            body_length_bytes: bodySizeBytes,
            chunk_size_bytes: this.chunkSizeBytes,
          },
          timeoutMs,
          { method: req.method, path: req.path, requestId, phase: 'http_request_init' },
        );

        const chunks = this.splitIntoUtf8SizedChunks(body, this.chunkSizeBytes);
        if (this.debug) {
          this.logger('[bridge] request:chunked:init_ok', { requestId, chunkCount: chunks.length });
        }
        for (let i = 0; i < chunks.length; i += 1) {
          if (this.debug) {
            this.logger('[bridge] request:chunked:chunk_send', {
              requestId,
              seq: i,
              total: chunks.length,
              chunkBytes: this.utf8ByteLength(chunks[i]),
            });
          }
          await this.sendMessage(
            `app:${this.clientId}`,
            'http_request_chunk',
            {
              request_id: requestId,
              session_id: this.sessionId,
              seq: i,
              chunk: chunks[i],
            },
            timeoutMs,
            { method: req.method, path: req.path, requestId, phase: 'http_request_chunk' },
          );
        }

        if (this.debug) {
          this.logger('[bridge] request:chunked:end_send', { requestId, finalSeq: chunks.length - 1 });
        }
        reply = await this.sendMessage(
          `app:${this.clientId}`,
          'http_request_end',
          {
            request_id: requestId,
            session_id: this.sessionId,
            final_seq: chunks.length - 1,
          },
          timeoutMs,
          { method: req.method, path: req.path, requestId, phase: 'http_request_end' },
        );

        if (this.debug) {
          this.logger('[bridge] request:chunked:end_reply', { requestId, reply });
        }
      } else {
        reply = await this.sendMessage(
          `app:${this.clientId}`,
          'http_request',
          {
            request_id: requestId,
            session_id: this.sessionId,
            method: req.method,
            path: req.path,
            headers,
            body,
          },
          timeoutMs,
          { method: req.method, path: req.path, requestId, phase: 'http_request' },
        );

        if (this.debug) {
          this.logger('[bridge] request:legacy:reply', { requestId, reply });
        }
      }

      const raw = await this.resolveHttpResponse({ requestId, reply, responsePromise });
      if (this.debug) {
        this.logger('[bridge] request:response_raw', {
          requestId,
          status: raw.status,
          bodyBytes: this.utf8ByteLength(raw.body || ''),
        });
      }
      const parsed = this.parseHttpResponse(raw);
      return parsed as { status: number; data: T };
    } catch (err) {
      // Ensure we don't leave a timed-out streaming response promise behind.
      this.cleanupStreamingResponse(requestId);
      throw err;
    }
  }

  private cleanupStreamingResponse(requestId: string): void {
    const state = this.streamingResponses.get(requestId);
    if (!state) {
      return;
    }
    clearTimeout(state.timeoutId);
    this.streamingResponses.delete(requestId);
  }

  async listServers(): Promise<BridgeServer[]> {
    const response = await this.sendMessage(`app:${this.clientId}`, 'list_servers', {});
    const servers = Array.isArray(response?.servers) ? response.servers : [];
    return servers as BridgeServer[];
  }

  async requestPairing(serverId: string): Promise<void> {
    this.serverId = serverId;
    await this.sendMessage(`app:${this.clientId}`, 'pair_request', { server_id: serverId });
  }

  async submitPairingCode(serverId: string, code: string): Promise<void> {
    const response = await this.sendMessage(`app:${this.clientId}`, 'pair_submit', {
      server_id: serverId,
      code,
    });
    this.sessionId = response.session_id;
    this.pairingToken = response.pairing_token || null;
    this.serverId = serverId;
  }

  private async ensureConnected(): Promise<void> {
    if (this.ws && this.ws.readyState === 1) {
      return;
    }

    if (!this.connectPromise) {
      this.connectPromise = this.connectInternal();
    }

    try {
      await this.connectPromise;
    } finally {
      this.connectPromise = null;
    }
  }

  private connectInternal(): Promise<void> {
    return new Promise((resolve, reject) => {
      const fullUrl = `${this.bridgeUrl}?type=app`;
      const ws = this.wsFactory(fullUrl);
      this.ws = ws;

      const timeoutId = setTimeout(() => {
        if (this.ws && this.ws.readyState !== 1) {
          this.ws.close();
        }
        reject(new Error('Connection timeout'));
      }, 10000);

      ws.onmessage = (event) => {
        let data: any;
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }

        const ref = data?.ref;
        if (ref && this.responseHandlers.has(ref)) {
          const handler = this.responseHandlers.get(ref)!;
          this.responseHandlers.delete(ref);
          handler(data);
          return;
        }

        // Server pushes (no ref).
        this.handlePushEvent(data);
      };

      ws.onopen = async () => {
        clearTimeout(timeoutId);
        try {
          await this.joinChannel();
          if (this.pairingToken && this.serverId && !this.sessionId) {
            await this.resumeSessionRaw();
          }
          resolve();
        } catch (err: any) {
          this.ws?.close();
          reject(err);
        }
      };

      ws.onerror = () => {
        clearTimeout(timeoutId);
        reject(new Error('WebSocket error'));
      };

      ws.onclose = (event) => {
        clearTimeout(timeoutId);
        this.ws = null;
        this.sessionId = null;

        const code = typeof event?.code === 'number' ? event.code : undefined;
        if (code && code !== 1000 && code !== 1005) {
          reject(new Error(`Connection closed unexpectedly (code: ${code})`));
        }
      };
    });
  }

  private getRef(): string {
    this.refCounter += 1;
    return this.refCounter.toString();
  }

  private async sendMessage(
    topic: string,
    event: string,
    payload: any,
    timeoutMs?: number,
    context?: { method?: string; path?: string; requestId?: string; phase?: string },
  ): Promise<any> {
    await this.ensureConnected();
    return this.sendMessageRaw(topic, event, payload, timeoutMs, context);
  }

  private sendMessageRaw(
    topic: string,
    event: string,
    payload: any,
    timeoutMs: number = 30000,
    context?: { method?: string; path?: string; requestId?: string; phase?: string },
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== 1) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const ref = this.getRef();
      const message = JSON.stringify({ topic, event, payload, ref });

      const timeoutId = setTimeout(() => {
        if (this.responseHandlers.has(ref)) {
          this.responseHandlers.delete(ref);
          reject(
            new Error(
              this.formatTimeoutError({
                timeoutMs,
                event,
                method: context?.method,
                path: context?.path,
                requestId: context?.requestId,
                phase: context?.phase,
              }),
            ),
          );
        }
      }, timeoutMs);

      this.responseHandlers.set(ref, (data) => {
        clearTimeout(timeoutId);
        if (data.event === 'phx_reply' && data.payload?.status === 'ok') {
          resolve(data.payload.response);
        } else {
          reject(
            new Error(
              this.formatBridgeError({
                error: data.payload?.response?.error || 'Request failed',
                event,
                method: context?.method,
                path: context?.path,
                requestId: context?.requestId,
                phase: context?.phase,
              }),
            ),
          );
        }
      });

      this.ws.send(message);
    });
  }

  private createStreamingResponsePromise(
    requestId: string,
    timeoutMs: number,
    context: { method: string; path: string },
  ): Promise<{ status: number; headers: Record<string, string>; body: string }> {
    // Prepare a buffer so we can transparently handle chunked responses.
    if (this.streamingResponses.has(requestId)) {
      this.streamingResponses.delete(requestId);
    }

    let resolveFn: any;
    let rejectFn: any;
    const promise = new Promise<{ status: number; headers: Record<string, string>; body: string }>(
      (resolve, reject) => {
        resolveFn = resolve;
        rejectFn = reject;
      },
    );

    const timeoutId = setTimeout(() => {
      const state = this.streamingResponses.get(requestId);
      if (!state) {
        return;
      }
      this.streamingResponses.delete(requestId);
      state.reject(new Error(`Request timeout (HTTP ${context.method} ${context.path})`));
    }, timeoutMs);

    this.streamingResponses.set(requestId, {
      status: null,
      headers: null,
      chunks: [],
      resolve: resolveFn,
      reject: rejectFn,
      timeoutId,
    });

    return promise;
  }

  private handlePushEvent(data: any): void {
    const event = data?.event;
    const payload = data?.payload || {};

    if (event === 'http_response_init') {
      const requestId = payload.request_id;
      const state = requestId ? this.streamingResponses.get(requestId) : null;
      if (!state) {
        return;
      }
      state.status = typeof payload.status === 'number' ? payload.status : 200;
      state.headers = (payload.headers && typeof payload.headers === 'object' ? payload.headers : {}) as Record<
        string,
        string
      >;

      if (this.debug) {
        this.logger('[bridge] response:chunked:init', {
          requestId,
          status: state.status,
          bodyLengthBytes: payload.body_length_bytes,
          chunkSizeBytes: payload.chunk_size_bytes,
        });
      }
      return;
    }

    if (event === 'http_response_chunk') {
      const requestId = payload.request_id;
      const state = requestId ? this.streamingResponses.get(requestId) : null;
      if (!state) {
        return;
      }
      const seq = typeof payload.seq === 'number' ? payload.seq : null;
      const chunk = typeof payload.chunk === 'string' ? payload.chunk : '';
      if (seq === null || seq !== state.chunks.length) {
        return;
      }
      state.chunks.push(chunk);

      if (this.debug) {
        this.logger('[bridge] response:chunked:chunk_recv', {
          requestId,
          seq,
          chunkBytes: this.utf8ByteLength(chunk),
        });
      }
      return;
    }

    if (event === 'http_response_end') {
      const requestId = payload.request_id;
      const state = requestId ? this.streamingResponses.get(requestId) : null;
      if (!state) {
        return;
      }
      const finalSeq = typeof payload.final_seq === 'number' ? payload.final_seq : null;
      if (finalSeq === null || finalSeq !== state.chunks.length - 1) {
        clearTimeout(state.timeoutId);
        this.streamingResponses.delete(requestId);
        state.reject(new Error('Invalid chunked response sequence'));
        return;
      }
      const status = state.status ?? 200;
      const headers = state.headers ?? {};
      const body = state.chunks.join('');

      if (this.debug) {
        this.logger('[bridge] response:chunked:end', {
          requestId,
          status,
          chunkCount: state.chunks.length,
          bodyBytes: this.utf8ByteLength(body),
        });
      }
      clearTimeout(state.timeoutId);
      this.streamingResponses.delete(requestId);
      state.resolve({ status, headers, body });
    }
  }

  private async resolveHttpResponse(options: {
    requestId: string;
    reply: any;
    responsePromise: Promise<{ status: number; headers: Record<string, string>; body: string }>;
  }): Promise<{ status: number; headers: Record<string, string>; body: string }> {
    const reply = options.reply;

    if (reply && typeof reply === 'object') {
      if ((reply as any).type === 'http_response_chunked' && (reply as any).request_id === options.requestId) {
        return await options.responsePromise;
      }

      if (typeof (reply as any).body === 'string' && typeof (reply as any).status === 'number') {
        // Legacy non-chunked response. Clean up any prepared streaming buffer.
        const state = this.streamingResponses.get(options.requestId);
        if (state) {
          clearTimeout(state.timeoutId);
          this.streamingResponses.delete(options.requestId);
        }
        return {
          status: (reply as any).status,
          headers: ((reply as any).headers || {}) as Record<string, string>,
          body: (reply as any).body || '',
        };
      }
    }

    // If the reply doesn't contain a full response, assume it was chunked.
    return await options.responsePromise;
  }

  private parseHttpResponse(raw: {
    status: number;
    headers: Record<string, string>;
    body: string;
  }): { status: number; data: any } {
    const status = raw.status;
    const headers = raw.headers || {};
    const contentType = String(
      headers['content-type'] || headers['Content-Type'] || headers['CONTENT-TYPE'] || '',
    );

    let data: any = null;
    if (contentType.includes('application/json')) {
      data = raw.body ? JSON.parse(raw.body) : null;
    } else {
      data = raw.body;
    }

    if (status >= 400) {
      const detail =
        typeof data === 'string'
          ? data
          : (data && typeof data === 'object' && 'detail' in data && (data as any).detail) ||
            JSON.stringify(data);
      throw new Error(`HTTP ${status} ${detail}`);
    }

    return { status, data };
  }

  private utf8ByteLength(value: string): number {
    const TE = (globalThis as any).TextEncoder as undefined | (new () => { encode: (s: string) => Uint8Array });
    if (TE) {
      return new TE().encode(value).length;
    }
    // Node fallback.
    const B = (globalThis as any).Buffer as undefined | { byteLength: (s: string, e?: string) => number };
    if (B) {
      return B.byteLength(value, 'utf8');
    }
    return value.length;
  }

  private splitIntoUtf8SizedChunks(value: string, chunkSizeBytes: number): string[] {
    // For ASCII/base64-heavy payloads, string length ≈ byte length.
    // To avoid expensive per-character UTF-8 sizing, slice by chars with a
    // small headroom for the Phoenix envelope + JSON escaping.
    const approxChars = Math.max(1, Math.floor(chunkSizeBytes - 2048));
    const chunks: string[] = [];
    for (let i = 0; i < value.length; i += approxChars) {
      chunks.push(value.slice(i, i + approxChars));
    }
    return chunks;
  }

  private resolveTimeoutMsForPath(path: string): number | undefined {
    let best: { pathPrefix: string; timeoutMs: number } | null = null;
    for (const rule of this.timeoutMsByPathPrefix) {
      if (!rule?.pathPrefix) {
        continue;
      }
      if (path.startsWith(rule.pathPrefix)) {
        if (!best || rule.pathPrefix.length > best.pathPrefix.length) {
          best = rule;
        }
      }
    }
    return best?.timeoutMs;
  }

  private formatTimeoutError(options: {
    timeoutMs: number;
    event: string;
    method?: string;
    path?: string;
    requestId?: string;
    phase?: string;
  }): string {
    const method = options.method || 'HTTP';
    const path = options.path || '(unknown path)';
    const phase = options.phase || options.event;
    return `Request timeout after ${options.timeoutMs}ms (HTTP ${method} ${path}, phase=${phase})`;
  }

  private formatBridgeError(options: {
    error: string;
    event: string;
    method?: string;
    path?: string;
    requestId?: string;
    phase?: string;
  }): string {
    const method = options.method || 'HTTP';
    const path = options.path || '(unknown path)';
    const phase = options.phase || options.event;
    return `${options.error} (HTTP ${method} ${path}, phase=${phase})`;
  }

  private async joinChannel(): Promise<void> {
    const topic = `app:${this.clientId}`;
    const ref = this.getRef();
    const msg = JSON.stringify({ topic, event: 'phx_join', payload: {}, ref });

    await new Promise<void>((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== 1) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      this.responseHandlers.set(ref, (data) => {
        if (data.event === 'phx_reply' && data.payload?.status === 'ok') {
          resolve();
        } else {
          reject(new Error('Failed to join channel'));
        }
      });

      this.ws.send(msg);
    });
  }

  private async resumeSessionRaw(): Promise<void> {
    if (!this.pairingToken || !this.serverId) {
      return;
    }

    const response = await this.sendMessageRaw(`app:${this.clientId}`, 'resume_session', {
      pairing_token: this.pairingToken,
      server_id: this.serverId,
    });

    this.sessionId = response.session_id;
  }
}
