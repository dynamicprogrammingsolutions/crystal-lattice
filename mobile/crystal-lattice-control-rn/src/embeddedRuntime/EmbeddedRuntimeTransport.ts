import type { HttpMethod, Transport } from "@crystal-lattice/frontend-sdk";

import { executeEmbeddedRuntimeCommand } from "./embeddedPythonRuntime";

export class EmbeddedRuntimeTransport implements Transport {
  async request<T = any>(request: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
    signal?: AbortSignal;
  }): Promise<{ status: number; data: T }> {
    if (request.signal?.aborted) {
      throw new Error(
        `Embedded runtime request aborted: ${request.method} ${request.path}`,
      );
    }

    const response = await executeEmbeddedRuntimeCommand<T>({
      method: request.method,
      path: request.path,
      headers: request.headers ?? {},
      body: request.body,
    });
    if (response.status < 200 || response.status >= 300) {
      const detail =
        response.data &&
        typeof response.data === "object" &&
        "detail" in response.data
          ? String((response.data as { detail?: unknown }).detail)
          : JSON.stringify(response.data);
      throw new Error(
        `Embedded runtime ${response.status} ${request.method} ${request.path}: ${detail}`,
      );
    }
    return response;
  }
}
