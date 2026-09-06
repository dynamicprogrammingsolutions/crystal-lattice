import {
  FetchTransport,
  RestAgentBackend,
  type AgentBackend,
  type ConnectionRecord,
  type ConnectionSessionStatusReader,
  type ConnectionSessionStatusResult,
} from '@crystal-lattice/frontend-sdk';

const STATUS_TIMEOUT_MS = 10_000;

function classifyReadError(error: unknown): ConnectionSessionStatusResult {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
      ? error
      : '';
  if (message.includes('HTTP 404') || message.includes('HTTP 405')) {
    return { status: 'unsupported' };
  }
  if (message.includes('HTTP 401') || message.includes('HTTP 403')) {
    return { status: 'unauthorized' };
  }
  return { status: 'unavailable', ...(message ? { message } : {}) };
}

async function readWithBackend(
  backend: AgentBackend,
  sessionIds: readonly string[],
  signal?: AbortSignal,
): Promise<ConnectionSessionStatusResult> {
  if (!backend.getSessionRequestStatuses) return { status: 'unsupported' };
  try {
    const snapshot = await backend.getSessionRequestStatuses(sessionIds, {
      signal,
    });
    if (signal?.aborted) return { status: 'unavailable' };
    return { status: 'ok', snapshot };
  } catch (error) {
    return classifyReadError(error);
  }
}

export class DesktopConnectionSessionStatusReader
  implements ConnectionSessionStatusReader
{
  constructor(
    private readonly getOpenBackend: (
      connectionId: string,
    ) => AgentBackend | null,
  ) {}

  async getSessionRequestStatuses(
    record: ConnectionRecord,
    sessionIds: readonly string[],
    options: { signal?: AbortSignal } = {},
  ): Promise<ConnectionSessionStatusResult> {
    if (sessionIds.length === 0) {
      return {
        status: 'ok',
        snapshot: {
          version: 1,
          authority: 'derived_transient',
          statuses: [],
          missing_session_ids: [],
        },
      };
    }
    const openBackend = this.getOpenBackend(record.id);
    if (openBackend) {
      return readWithBackend(openBackend, sessionIds, options.signal);
    }
    if (record.kind !== 'manual') {
      return { status: 'unsupported' };
    }
    const backend = new RestAgentBackend({
      transport: new FetchTransport({
        baseUrl: `http://${record.host}:${record.port}`,
        defaultRequestTimeoutMs: STATUS_TIMEOUT_MS,
      }),
    });
    return readWithBackend(backend, sessionIds, options.signal);
  }
}
