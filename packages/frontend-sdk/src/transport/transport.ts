export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface Transport {
  request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }>;
}
