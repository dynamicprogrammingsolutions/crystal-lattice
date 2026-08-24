import type { BridgeServer } from './bridgeTransport';
import { BridgeTransport } from './bridgeTransport';
import type {
  BridgeConnectionTransport,
  BridgeConnectionTransportOptions,
} from './bridgeConnectionTransport';
import { HttpBridgeTransport } from './httpBridgeTransport';
import type { HttpMethod } from './transport';

export type LegacyBridgeTransportFactory = (options: {
  bridgeUrl: string;
  serverId: string;
  pairingToken: string;
}) => BridgeConnectionTransport;

export class HybridBridgeTransport implements BridgeConnectionTransport {
  private readonly options: BridgeConnectionTransportOptions;
  private readonly httpTransport: HttpBridgeTransport;
  private readonly legacyTransportFactory: LegacyBridgeTransportFactory;
  private legacyTransport: BridgeConnectionTransport | null = null;

  constructor(
    options: BridgeConnectionTransportOptions & {
      legacyTransportFactory?: LegacyBridgeTransportFactory;
    },
  ) {
    this.options = options;
    this.httpTransport = new HttpBridgeTransport(options);
    this.legacyTransportFactory =
      options.legacyTransportFactory ??
      ((legacyOptions) =>
        new BridgeTransport({
          bridgeUrl: legacyOptions.bridgeUrl,
          serverId: legacyOptions.serverId,
          pairingToken: legacyOptions.pairingToken,
          wsFactory: options.wsFactory,
          defaultRequestTimeoutMs: options.defaultRequestTimeoutMs,
          connectTimeoutMs: options.connectTimeoutMs,
          heartbeatIntervalMs: options.heartbeatIntervalMs,
          heartbeatTimeoutMs: options.heartbeatTimeoutMs,
          debug: options.debug,
          logger: options.logger,
          timeoutRules: options.timeoutRules,
          timeoutMsByPathPrefix: options.timeoutMsByPathPrefix,
        }));
  }

  getPairingToken(): string | null {
    return this.httpTransport.getPairingToken();
  }

  getServerId(): string | null {
    return this.httpTransport.getServerId();
  }

  isPaired(): boolean {
    return this.httpTransport.isPaired();
  }

  async connect(): Promise<void> {
    await this.httpTransport.connect();
    if (this.httpTransport.isPaired()) {
      await this.ensureLegacyTransport();
    }
  }

  disconnect(): void {
    this.httpTransport.disconnect();
    this.legacyTransport?.disconnect();
  }

  prepareForResume(): void {
    this.httpTransport.prepareForResume();
    this.legacyTransport?.prepareForResume();
  }

  async listServers(): Promise<BridgeServer[]> {
    return await this.httpTransport.listServers();
  }

  async requestPairing(serverId: string): Promise<void> {
    await this.httpTransport.requestPairing(serverId);
  }

  async submitPairingCode(serverId: string, code: string): Promise<void> {
    await this.httpTransport.submitPairingCode(serverId, code);
    this.legacyTransport?.disconnect();
    this.legacyTransport = null;
    await this.ensureLegacyTransport();
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    if (isLegacyEventRequest(req.method, req.path)) {
      const legacy = await this.ensureLegacyTransport();
      return await legacy.request<T>(req);
    }
    return await this.httpTransport.request<T>(req);
  }

  private async ensureLegacyTransport(): Promise<BridgeConnectionTransport> {
    const serverId = this.httpTransport.getServerId();
    const pairingToken = this.httpTransport.getPairingToken();
    if (!serverId || !pairingToken) {
      throw new Error('Not paired with any server');
    }
    if (!this.legacyTransport) {
      this.legacyTransport = this.legacyTransportFactory({
        bridgeUrl: this.options.bridgeUrl,
        serverId,
        pairingToken,
      });
    }
    await this.legacyTransport.connect();
    return this.legacyTransport;
  }
}

export function isLegacyEventRequest(method: HttpMethod, path: string): boolean {
  return method === 'GET' && (path === '/events' || path.startsWith('/events?'));
}
