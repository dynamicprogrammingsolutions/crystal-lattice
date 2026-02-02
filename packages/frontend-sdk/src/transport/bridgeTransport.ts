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

  private responseHandlers: Map<string, (data: any) => void> = new Map();

  private serverId: string | null = null;
  private pairingToken: string | null = null;
  private sessionId: string | null = null;

  constructor(options: {
    bridgeUrl: string;
    serverId?: string | null;
    pairingToken?: string | null;
    wsFactory?: WebSocketFactory;
    clientId?: string;
  }) {
    this.bridgeUrl = options.bridgeUrl;
    this.serverId = options.serverId ?? null;
    this.pairingToken = options.pairingToken ?? null;
    this.clientId = options.clientId ?? generateUuid();

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

    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: generateUuid(),
        session_id: this.sessionId,
        method: req.method,
        path: req.path,
        headers: req.headers || {},
        body: req.body === undefined ? null : JSON.stringify(req.body),
      },
      req.timeoutMs,
    );

    let data: any = response;
    if (response && typeof response === 'object' && typeof (response as any).body === 'string') {
      const rawBody = (response as any).body;
      if (rawBody) {
        data = JSON.parse(rawBody);
      }
    }

    return { status: 200, data: data as T };
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
        }
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
  ): Promise<any> {
    await this.ensureConnected();
    return this.sendMessageRaw(topic, event, payload, timeoutMs);
  }

  private sendMessageRaw(
    topic: string,
    event: string,
    payload: any,
    timeoutMs: number = 30000,
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
          reject(new Error('Request timeout'));
        }
      }, timeoutMs);

      this.responseHandlers.set(ref, (data) => {
        clearTimeout(timeoutId);
        if (data.event === 'phx_reply' && data.payload?.status === 'ok') {
          resolve(data.payload.response);
        } else {
          reject(new Error(data.payload?.response?.error || 'Request failed'));
        }
      });

      this.ws.send(message);
    });
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
