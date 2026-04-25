import type {
  HttpMethod,
  PathPrefixTimeoutRule,
  Transport,
  TransportTimeoutRule,
} from './transport';
import { resolveTransportTimeoutMs } from './transport';

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
  private readonly connectTimeoutMs: number;
  private readonly heartbeatIntervalMs: number;
  private readonly heartbeatTimeoutMs: number;
  private readonly debug: boolean;
  private readonly logger: (msg: string, meta?: any) => void;
  private readonly timeoutRules: TransportTimeoutRule[];
  private readonly timeoutMsByPathPrefix: PathPrefixTimeoutRule[];
  private heartbeatIntervalId: ReturnType<typeof setInterval> | null = null;
  private heartbeatInFlight = false;
  private connectionGeneration = 0;
  private forceValidateBeforeNextRequest = false;
  private validationPromise: Promise<void> | null = null;
  private lastSocketActivityAtMs = 0;
  private lastHeartbeatOkAtMs = 0;

  private pendingReplies: Map<
    string,
    {
      timeoutId: any;
      resolve: (value: any) => void;
      reject: (err: any) => void;
      event: string;
      context?: {
        method?: string;
        path?: string;
        requestId?: string;
        phase?: string;
        resetSocketOnTimeout?: boolean;
      };
    }
  > = new Map();
  private streamingResponses: Map<
    string,
    {
      status: number | null;
      headers: Record<string, string> | null;
      chunks: string[];
      resolve: (resp: { status: number; headers: Record<string, string>; body: string }) => void;
      reject: (err: any) => void;
      timeoutId: any;
      context: {
        method: string;
        path: string;
        resetSocketOnTimeout: boolean;
      };
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
    connectTimeoutMs?: number;
    heartbeatIntervalMs?: number;
    heartbeatTimeoutMs?: number;
    debug?: boolean;
    logger?: (msg: string, meta?: any) => void;
    timeoutRules?: TransportTimeoutRule[];
    timeoutMsByPathPrefix?: PathPrefixTimeoutRule[];
  }) {
    this.bridgeUrl = options.bridgeUrl;
    this.serverId = options.serverId ?? null;
    this.pairingToken = options.pairingToken ?? null;
    this.clientId = options.clientId ?? generateUuid();

    this.chunkingThresholdBytes = options.chunkingThresholdBytes ?? 256 * 1024;
    // Keep a safe headroom so the Phoenix envelope stays < ~1MiB.
    this.chunkSizeBytes = options.chunkSizeBytes ?? 900 * 1024;
    this.defaultRequestTimeoutMs = options.defaultRequestTimeoutMs ?? 120_000;
    this.connectTimeoutMs = options.connectTimeoutMs ?? 10_000;
    this.heartbeatIntervalMs = options.heartbeatIntervalMs ?? 15_000;
    this.heartbeatTimeoutMs = options.heartbeatTimeoutMs ?? 5_000;
    this.debug = options.debug ?? false;
    this.logger = options.logger ?? ((msg: string, meta?: any) => console.log(msg, meta ?? ''));
    this.timeoutRules = options.timeoutRules ?? [];
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

  prepareForResume(): void {
    this.forceValidateBeforeNextRequest = true;
  }

  disconnect(): void {
    this.resetSocket(new Error('Disconnected'), { reason: 'disconnect', closeSocket: true });
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
    const timeoutMs = resolveTransportTimeoutMs({
      method: req.method,
      path: req.path,
      timeoutMs: req.timeoutMs,
      defaultRequestTimeoutMs: this.defaultRequestTimeoutMs,
      timeoutRules: this.timeoutRules,
      timeoutMsByPathPrefix: this.timeoutMsByPathPrefix,
    })!;
    const resetSocketOnTimeout = this.shouldResetSocketOnRequestTimeout(req.method, req.path);
    const responsePromise = this.createStreamingResponsePromise(requestId, timeoutMs, {
      method: req.method,
      path: req.path,
      resetSocketOnTimeout,
    });
    // This promise may time out before we ever `await` it (e.g. legacy requests).
    // Attach a handler so a timeout can't surface as an unhandled rejection.
    responsePromise.catch(() => {
      // Intentionally ignored; the main request promise will surface errors.
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
          {
            method: req.method,
            path: req.path,
            requestId,
            phase: 'http_request_init',
            resetSocketOnTimeout,
          },
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
            {
              method: req.method,
              path: req.path,
              requestId,
              phase: 'http_request_chunk',
              resetSocketOnTimeout,
            },
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
          {
            method: req.method,
            path: req.path,
            requestId,
            phase: 'http_request_end',
            resetSocketOnTimeout,
          },
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
          {
            method: req.method,
            path: req.path,
            requestId,
            phase: 'http_request',
            resetSocketOnTimeout,
          },
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
    const response = await this.sendMessage(`app:${this.clientId}`, 'list_servers', {}, undefined, {
      phase: 'list_servers',
      resetSocketOnTimeout: true,
    });
    const servers = Array.isArray(response?.servers) ? response.servers : [];
    return servers as BridgeServer[];
  }

  async requestPairing(serverId: string): Promise<void> {
    this.serverId = serverId;
    await this.sendMessage(
      `app:${this.clientId}`,
      'pair_request',
      { server_id: serverId },
      undefined,
      { phase: 'pair_request', resetSocketOnTimeout: true },
    );
  }

  async submitPairingCode(serverId: string, code: string): Promise<void> {
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'pair_submit',
      {
        server_id: serverId,
        code,
      },
      undefined,
      { phase: 'pair_submit', resetSocketOnTimeout: true },
    );
    this.sessionId = response.session_id;
    this.pairingToken = response.pairing_token || null;
    this.serverId = serverId;
  }

  private async ensureConnected(): Promise<void> {
    if (this.ws && this.ws.readyState === 1) {
      if (this.shouldValidateCurrentSocket()) {
        try {
          await this.validateCurrentSocket();
        } catch {
          await this.connectFresh();
        }
      }
      return;
    }

    await this.connectFresh();
  }

  private async connectFresh(): Promise<void> {
    if (!this.connectPromise) {
      this.connectPromise = this.connectInternal();
    }

    try {
      await this.connectPromise;
    } finally {
      this.connectPromise = null;
    }
  }

  private shouldValidateCurrentSocket(): boolean {
    if (!this.ws || this.ws.readyState !== 1) {
      return false;
    }
    if (this.forceValidateBeforeNextRequest) {
      return true;
    }
    if (this.heartbeatIntervalMs <= 0 || this.heartbeatTimeoutMs <= 0) {
      return false;
    }

    const lastKnownGood = Math.max(this.lastSocketActivityAtMs, this.lastHeartbeatOkAtMs);
    if (lastKnownGood <= 0) {
      return false;
    }
    const staleAfterMs = this.heartbeatIntervalMs + this.heartbeatTimeoutMs + 1_000;
    return Date.now() - lastKnownGood > staleAfterMs;
  }

  private async validateCurrentSocket(): Promise<void> {
    if (!this.ws || this.ws.readyState !== 1) {
      throw new Error('WebSocket not connected');
    }
    if (this.validationPromise) {
      return this.validationPromise;
    }

    this.validationPromise = (async () => {
      this.debugLog('[bridge] validate:send', {
        generation: this.connectionGeneration,
        timeoutMs: this.heartbeatTimeoutMs,
        forced: this.forceValidateBeforeNextRequest,
      });
      await this.sendMessageRaw('phoenix', 'heartbeat', {}, this.heartbeatTimeoutMs, {
        phase: 'heartbeat_validation',
        resetSocketOnTimeout: true,
      });
      this.forceValidateBeforeNextRequest = false;
      this.markSocketActivity();
      this.lastHeartbeatOkAtMs = Date.now();
      this.debugLog('[bridge] validate:ok', {
        generation: this.connectionGeneration,
      });
    })();

    try {
      await this.validationPromise;
    } finally {
      this.validationPromise = null;
    }
  }

  private connectInternal(): Promise<void> {
    return new Promise((resolve, reject) => {
      const fullUrl = `${this.bridgeUrl}?type=app`;
      const ws = this.wsFactory(fullUrl);
      const connectionGeneration = ++this.connectionGeneration;
      this.ws = ws;
      let settled = false;

      const resolveOnce = () => {
        if (settled) {
          return;
        }
        settled = true;
        resolve();
      };

      const rejectOnce = (err: Error) => {
        if (settled) {
          return;
        }
        settled = true;
        reject(err);
      };

      const isCurrentSocket = () => this.ws === ws && this.connectionGeneration === connectionGeneration;

      this.debugLog('[bridge] connect:start', {
        generation: connectionGeneration,
        bridgeUrl: this.bridgeUrl,
      });

      const timeoutId = setTimeout(() => {
        if (!isCurrentSocket()) {
          return;
        }
        const err = new Error('Connection timeout');
        this.resetSocket(err, {
          reason: 'connect_timeout',
          socket: ws,
          closeSocket: true,
        });
        rejectOnce(err);
      }, this.connectTimeoutMs);

      ws.onmessage = (event) => {
        if (!isCurrentSocket()) {
          return;
        }
        let data: any;
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }

        const ref = data?.ref;
        if (ref) {
          const pending = this.pendingReplies.get(ref);
          if (pending) {
            this.pendingReplies.delete(ref);
            clearTimeout(pending.timeoutId);

            if (data.event === 'phx_reply' && data.payload?.status === 'ok') {
              this.markSocketActivity();
              if (
                pending.context?.phase === 'heartbeat' ||
                pending.context?.phase === 'heartbeat_validation'
              ) {
                this.lastHeartbeatOkAtMs = Date.now();
                this.debugLog('[bridge] heartbeat:ok', { generation: connectionGeneration });
              }
              pending.resolve(data.payload.response);
            } else {
              const response = data?.payload?.response;
              pending.reject(
                new Error(
                  this.formatBridgeError({
                    error:
                      response?.error ||
                      response?.reason ||
                      data?.payload?.reason ||
                      'Request failed',
                    event: pending.event,
                    method: pending.context?.method,
                    path: pending.context?.path,
                    requestId: pending.context?.requestId,
                    phase: pending.context?.phase,
                  }),
                ),
              );
            }
            return;
          }
        }

        // Server pushes (no ref).
        this.handlePushEvent(data);
      };

      ws.onopen = async () => {
        clearTimeout(timeoutId);
        if (!isCurrentSocket()) {
          return;
        }
        this.debugLog('[bridge] connect:open', { generation: connectionGeneration });
        try {
          await this.joinChannel();
          if (this.pairingToken && this.serverId && !this.sessionId) {
            await this.resumeSessionRaw();
          }
          this.forceValidateBeforeNextRequest = false;
          this.markSocketActivity();
          this.startHeartbeat(connectionGeneration);
          resolveOnce();
        } catch (err: any) {
          const error = err instanceof Error ? err : new Error(String(err));
          this.resetSocket(error, {
            reason: 'connect_setup_failed',
            socket: ws,
            closeSocket: true,
          });
          rejectOnce(error);
        }
      };

      ws.onerror = () => {
        clearTimeout(timeoutId);
        if (!isCurrentSocket()) {
          return;
        }
        const err = new Error('WebSocket error');
        this.resetSocket(err, {
          reason: 'ws_error',
          socket: ws,
          closeSocket: true,
        });
        rejectOnce(err);
      };

      ws.onclose = (event) => {
        clearTimeout(timeoutId);
        if (!isCurrentSocket()) {
          return;
        }
        const code = typeof event?.code === 'number' ? event.code : undefined;
        const reason = typeof event?.reason === 'string' ? event.reason : undefined;
        const closeError = new Error(
          `Connection closed${code ? ` (code: ${code})` : ''}${reason ? `: ${reason}` : ''}`,
        );
        this.resetSocket(closeError, {
          reason: 'ws_close',
          socket: ws,
          closeSocket: false,
          meta: { code, reason, wasClean: event?.wasClean },
        });

        if (!settled) {
          rejectOnce(
            code && code !== 1000 && code !== 1005
              ? new Error(`Connection closed unexpectedly (code: ${code})`)
              : closeError,
          );
        }
      };
    });
  }

  private failAllPendingReplies(err: Error): void {
    if (this.pendingReplies.size === 0) {
      return;
    }

    for (const pending of this.pendingReplies.values()) {
      clearTimeout(pending.timeoutId);
      try {
        pending.reject(err);
      } catch {
        // Ignore failures from userland promise handlers.
      }
    }

    this.pendingReplies.clear();
  }

  private failAllStreamingResponses(err: Error): void {
    if (this.streamingResponses.size === 0) {
      return;
    }

    for (const state of this.streamingResponses.values()) {
      clearTimeout(state.timeoutId);
      try {
        state.reject(err);
      } catch {
        // Ignore failures from userland promise handlers.
      }
    }

    this.streamingResponses.clear();
  }

  private resetSocket(
    err: Error,
    options: {
      reason: string;
      socket?: WebSocketLike | null;
      closeSocket?: boolean;
      meta?: Record<string, any>;
    },
  ): void {
    const socket = options.socket ?? this.ws;
    const shouldCloseSocket = options.closeSocket !== false;

    this.debugLog('[bridge] socket:reset', {
      reason: options.reason,
      error: err.message,
      sessionId: this.sessionId,
      serverId: this.serverId,
      ...options.meta,
    });

    this.stopHeartbeat();
    this.validationPromise = null;
    this.forceValidateBeforeNextRequest = false;
    this.lastSocketActivityAtMs = 0;
    this.lastHeartbeatOkAtMs = 0;
    this.failAllPendingReplies(err);
    this.failAllStreamingResponses(err);

    if (socket) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
    }

    if (this.ws === socket) {
      this.ws = null;
    }
    this.sessionId = null;

    if (socket && shouldCloseSocket) {
      try {
        socket.close();
      } catch {
        // Ignore close failures.
      }
    }
  }

  private getRef(): string {
    this.refCounter += 1;
    return this.refCounter.toString();
  }

  private markSocketActivity(): void {
    this.lastSocketActivityAtMs = Date.now();
  }

  private async sendMessage(
    topic: string,
    event: string,
    payload: any,
    timeoutMs?: number,
    context?: {
      method?: string;
      path?: string;
      requestId?: string;
      phase?: string;
      resetSocketOnTimeout?: boolean;
    },
  ): Promise<any> {
    await this.ensureConnected();
    return this.sendMessageRaw(topic, event, payload, timeoutMs, context);
  }

  private sendMessageRaw(
    topic: string,
    event: string,
    payload: any,
    timeoutMs: number = 30000,
    context?: {
      method?: string;
      path?: string;
      requestId?: string;
      phase?: string;
      resetSocketOnTimeout?: boolean;
    },
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== 1) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const ref = this.getRef();
      const message = JSON.stringify({ topic, event, payload, ref });

      const timeoutId = setTimeout(() => {
        const pending = this.pendingReplies.get(ref);
        if (!pending) {
          return;
        }
        this.pendingReplies.delete(ref);
        const err = new Error(
          this.formatTimeoutError({
            timeoutMs,
            event,
            method: context?.method,
            path: context?.path,
            requestId: context?.requestId,
            phase: context?.phase,
          }),
        );
        this.debugLog('[bridge] request:timeout', {
          event,
          method: context?.method,
          path: context?.path,
          requestId: context?.requestId,
          phase: context?.phase,
          timeoutMs,
          resetSocketOnTimeout: context?.resetSocketOnTimeout ?? false,
        });
        if (context?.resetSocketOnTimeout) {
          this.resetSocket(err, {
            reason: 'reply_timeout',
            closeSocket: true,
            meta: {
              event,
              method: context.method,
              path: context.path,
              requestId: context.requestId,
              phase: context.phase,
            },
          });
        }
        reject(err);
      }, timeoutMs);

      this.pendingReplies.set(ref, { timeoutId, resolve, reject, event, context });

      try {
        this.ws.send(message);
      } catch (err: any) {
        clearTimeout(timeoutId);
        this.pendingReplies.delete(ref);
        this.resetSocket(err instanceof Error ? err : new Error(String(err)), {
          reason: 'send_failed',
          closeSocket: true,
          meta: {
            event,
            method: context?.method,
            path: context?.path,
            requestId: context?.requestId,
            phase: context?.phase,
          },
        });
        reject(err);
      }
    });
  }

  private createStreamingResponsePromise(
    requestId: string,
    timeoutMs: number,
    context: { method: string; path: string; resetSocketOnTimeout: boolean },
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
      const err = new Error(`Request timeout (HTTP ${context.method} ${context.path})`);
      this.debugLog('[bridge] response:timeout', {
        requestId,
        method: context.method,
        path: context.path,
        timeoutMs,
        resetSocketOnTimeout: context.resetSocketOnTimeout,
      });
      if (context.resetSocketOnTimeout) {
        this.resetSocket(err, {
          reason: 'response_timeout',
          closeSocket: true,
          meta: {
            requestId,
            method: context.method,
            path: context.path,
          },
        });
      }
      state.reject(err);
    }, timeoutMs);

    this.streamingResponses.set(requestId, {
      status: null,
      headers: null,
      chunks: [],
      resolve: resolveFn,
      reject: rejectFn,
      timeoutId,
      context,
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

  private shouldResetSocketOnRequestTimeout(method: HttpMethod, path: string): boolean {
    return !(method === 'GET' && (path === '/events' || path.startsWith('/events?')));
  }

  private startHeartbeat(connectionGeneration: number): void {
    this.stopHeartbeat();
    if (this.heartbeatIntervalMs <= 0) {
      return;
    }

    this.heartbeatIntervalId = setInterval(() => {
      if (connectionGeneration !== this.connectionGeneration) {
        return;
      }
      this.sendHeartbeat(connectionGeneration).catch(() => {
        // Heartbeat failures already trigger reset and logging.
      });
    }, this.heartbeatIntervalMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
      this.heartbeatIntervalId = null;
    }
    this.heartbeatInFlight = false;
  }

  private async sendHeartbeat(connectionGeneration: number): Promise<void> {
    if (this.heartbeatInFlight) {
      return;
    }
    if (!this.ws || this.ws.readyState !== 1 || connectionGeneration !== this.connectionGeneration) {
      return;
    }

    this.heartbeatInFlight = true;
    this.debugLog('[bridge] heartbeat:send', { generation: connectionGeneration });
    try {
      await this.sendMessageRaw('phoenix', 'heartbeat', {}, this.heartbeatTimeoutMs, {
        phase: 'heartbeat',
        resetSocketOnTimeout: true,
      });
    } catch (err) {
      this.debugLog('[bridge] heartbeat:error', {
        generation: connectionGeneration,
        error: err instanceof Error ? err.message : String(err),
      });
      throw err;
    } finally {
      this.heartbeatInFlight = false;
    }
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
    if (!options.method && !options.path) {
      return `Request timeout after ${options.timeoutMs}ms (phase=${phase})`;
    }
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
    const phase = options.phase || options.event;
    if (!options.method && !options.path) {
      return `${options.error} (phase=${phase})`;
    }
    const method = options.method || 'HTTP';
    const path = options.path || '(unknown path)';
    return `${options.error} (HTTP ${method} ${path}, phase=${phase})`;
  }

  private async joinChannel(): Promise<void> {
    const topic = `app:${this.clientId}`;
    await this.sendMessageRaw(topic, 'phx_join', {}, this.connectTimeoutMs, {
      phase: 'phx_join',
      resetSocketOnTimeout: true,
    });
    this.debugLog('[bridge] join:ok', { clientId: this.clientId });
  }

  private async resumeSessionRaw(): Promise<void> {
    if (!this.pairingToken || !this.serverId) {
      return;
    }

    const response = await this.sendMessageRaw(`app:${this.clientId}`, 'resume_session', {
      pairing_token: this.pairingToken,
      server_id: this.serverId,
    }, this.connectTimeoutMs, {
      phase: 'resume_session',
      resetSocketOnTimeout: true,
    });

    this.sessionId = response.session_id;
    this.debugLog('[bridge] resume:ok', {
      clientId: this.clientId,
      serverId: this.serverId,
      sessionId: this.sessionId,
    });
  }

  private debugLog(msg: string, meta?: any): void {
    if (this.debug) {
      this.logger(msg, meta);
    }
  }
}
