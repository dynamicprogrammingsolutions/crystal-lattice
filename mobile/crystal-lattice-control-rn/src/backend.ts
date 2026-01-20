import type { ConnectionAdapter } from '../App';
import { RestAgentBackend, type Transport, type HttpMethod } from '@crystal-lattice/frontend-sdk';

class ConnectionAdapterTransport implements Transport {
  private adapter: ConnectionAdapter;

  constructor(adapter: ConnectionAdapter) {
    this.adapter = adapter;
  }

  async request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    // ConnectionAdapter already encapsulates direct HTTP vs bridge.
    // It throws on errors; we treat successful calls as status=200.
    const { method, path, body } = req;

    let data: any;
    if (method === 'GET') {
      data = await this.adapter.get(path);
    } else if (method === 'POST') {
      data = await this.adapter.post(path, body ?? {});
    } else if (method === 'PUT') {
      data = await this.adapter.put(path, body ?? {});
    } else if (method === 'PATCH') {
      data = await this.adapter.patch(path, body ?? {});
    } else if (method === 'DELETE') {
      data = await this.adapter.delete(path, body);
    } else {
      throw new Error(`Unsupported method: ${method}`);
    }

    return { status: 200, data };
  }
}

export function createAgentBackend(adapter: ConnectionAdapter): RestAgentBackend {
  return new RestAgentBackend({ transport: new ConnectionAdapterTransport(adapter) });
}
