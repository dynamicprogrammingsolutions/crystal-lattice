import type { AgentBackend } from '../backend/backend';
import {
  createMethodSuccessEventMiddleware,
  type BackendCallContext,
  type BackendMiddleware,
} from '../runtime/eventedBackend';
import type { SdkEvent } from '../runtime/sdkEvent';

type BackendMethodName = keyof AgentBackend;
type SessionScopedMethodName = {
  [K in BackendMethodName]: AgentBackend[K] extends (
    sessionId: string,
    ...args: any[]
  ) => Promise<any>
    ? K
    : never;
}[BackendMethodName];

export interface SessionScopedSuccessEventMiddlewareOptions<M extends SessionScopedMethodName> {
  method: M;
  eventType: string;
  mapEvent?: (options: {
    method: M;
    scopeKey: string;
    sessionId: string;
    args: Parameters<AgentBackend[M]>;
    result: Awaited<ReturnType<AgentBackend[M]>>;
    context: BackendCallContext<M>;
  }) => SdkEvent | SdkEvent[] | null | undefined;
}

function getSessionIdArg(args: unknown[]): string | null {
  const first = args[0];
  return typeof first === 'string' && first ? first : null;
}

export function createSessionScopedSuccessEventMiddleware<M extends SessionScopedMethodName>(
  options: SessionScopedSuccessEventMiddlewareOptions<M>,
): BackendMiddleware {
  const { method, eventType, mapEvent } = options;

  return createMethodSuccessEventMiddleware({
    method,
    buildEvent: ({ context, args, result }) => {
      const sessionId = getSessionIdArg(args as unknown[]);
      if (!sessionId) {
        return null;
      }

      if (mapEvent) {
        return mapEvent({
          method,
          scopeKey: context.scopeKey,
          sessionId,
          args,
          result,
          context,
        });
      }

      return {
        type: eventType,
        scopeKey: context.scopeKey,
        sessionId,
      };
    },
  });
}
