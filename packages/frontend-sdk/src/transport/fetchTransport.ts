import type {
  HttpMethod,
  PathPrefixTimeoutRule,
  Transport,
  TransportTimeoutRule,
} from './transport';
import { resolveTransportTimeoutMs } from './transport';

export class FetchTransport implements Transport {
  private baseUrl: string;
  private fetchImpl: typeof fetch;
  private readonly defaultRequestTimeoutMs?: number;
  private readonly debug: boolean;
  private readonly logger: (msg: string, meta?: any) => void;
  private readonly timeoutRules: TransportTimeoutRule[];
  private readonly timeoutMsByPathPrefix: PathPrefixTimeoutRule[];

  constructor(options: {
    baseUrl: string;
    fetchImpl?: typeof fetch;
    defaultRequestTimeoutMs?: number;
    debug?: boolean;
    logger?: (msg: string, meta?: any) => void;
    timeoutRules?: TransportTimeoutRule[];
    timeoutMsByPathPrefix?: PathPrefixTimeoutRule[];
  }) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.defaultRequestTimeoutMs = options.defaultRequestTimeoutMs;
    this.debug = options.debug ?? false;
    this.logger = options.logger ?? ((msg: string, meta?: any) => console.log(msg, meta ?? ''));
    this.timeoutRules = options.timeoutRules ?? [];
    this.timeoutMsByPathPrefix = options.timeoutMsByPathPrefix ?? [];
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
    signal?: AbortSignal;
  }): Promise<{ status: number; data: T }> {
    const url = `${this.baseUrl}${req.path}`;
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
    };

    let body: any = undefined;
    if (req.body !== undefined) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
      body = JSON.stringify(req.body);
    }

    const controller = typeof AbortController === 'function' ? new AbortController() : null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let didTimeout = false;
    const abortFromExternal = () => controller?.abort();
    if (req.signal?.aborted) {
      controller?.abort();
    } else {
      req.signal?.addEventListener('abort', abortFromExternal);
    }

    if (this.debug) {
      this.logger('[fetch] request:start', {
        method: req.method,
        path: req.path,
        timeoutMs,
      });
    }

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
        signal: controller?.signal ?? req.signal,
      });
    } catch (err: any) {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      if (didTimeout) {
        const timeoutError = new Error(
          `Request timeout after ${timeoutMs}ms (HTTP ${req.method} ${req.path})`,
        );
        if (this.debug) {
          this.logger('[fetch] request:timeout', {
            method: req.method,
            path: req.path,
            timeoutMs,
          });
        }
        throw timeoutError;
      }

      if (this.debug) {
        this.logger('[fetch] request:error', {
          method: req.method,
          path: req.path,
          error: err instanceof Error ? err.message : String(err),
        });
      }
      throw err;
    } finally {
      req.signal?.removeEventListener('abort', abortFromExternal);
    }

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    const status = resp.status;
    const contentType = resp.headers.get('content-type') || '';

    let data: any = null;
    if (contentType.includes('application/json')) {
      data = await resp.json();
    } else {
      data = await resp.text();
    }

    if (!resp.ok) {
      const detail =
        typeof data === 'string'
          ? data
          : (data && typeof data === 'object' && 'detail' in data && (data as any).detail) ||
            JSON.stringify(data);
      if (this.debug) {
        this.logger('[fetch] request:error', {
          method: req.method,
          path: req.path,
          status,
          detail,
        });
      }
      throw new Error(`HTTP ${status} ${req.method} ${req.path}: ${detail}`);
    }

    if (this.debug) {
      this.logger('[fetch] request:success', {
        method: req.method,
        path: req.path,
        status,
      });
    }

    return { status, data: data as T };
  }
}
