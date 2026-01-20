import type { HttpMethod, Transport } from './transport';

export class FetchTransport implements Transport {
  private baseUrl: string;
  private fetchImpl: typeof fetch;

  constructor(options: { baseUrl: string; fetchImpl?: typeof fetch }) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    const url = `${this.baseUrl}${req.path}`;

    const headers: Record<string, string> = {
      ...(req.headers || {}),
    };

    let body: any = undefined;
    if (req.body !== undefined) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
      body = JSON.stringify(req.body);
    }

    const resp = await this.fetchImpl(url, {
      method: req.method,
      headers,
      body,
    });

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
      throw new Error(`HTTP ${status} ${req.method} ${req.path}: ${detail}`);
    }

    return { status, data: data as T };
  }
}
