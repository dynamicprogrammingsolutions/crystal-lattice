import type { AgentBackend } from '../backend/backend';
import type { SdkEvent } from './sdkEvent';
import type { SdkEventBus } from './sdkEventBus';

type BackendMethodName = keyof AgentBackend;
type AsyncBackendMethodName = {
  [K in BackendMethodName]: AgentBackend[K] extends (...args: any[]) => Promise<any> ? K : never;
}[BackendMethodName];
type UnknownAsyncFn = (...args: any[]) => Promise<unknown>;

export interface BackendCallContext<M extends AsyncBackendMethodName = AsyncBackendMethodName> {
  method: M;
  args: Parameters<AgentBackend[M]>;
  scopeKey: string;
  backend: AgentBackend;
  bus: SdkEventBus;
  meta: Record<string, unknown>;
}

export type BackendCallNext = () => Promise<unknown>;

export type BackendMiddleware = (
  context: BackendCallContext,
  next: BackendCallNext,
) => Promise<unknown>;

export interface MethodSuccessEventMiddlewareOptions<M extends AsyncBackendMethodName> {
  method: M;
  buildEvent: (options: {
    context: BackendCallContext<M>;
    args: Parameters<AgentBackend[M]>;
    result: Awaited<ReturnType<AgentBackend[M]>>;
  }) => SdkEvent | SdkEvent[] | null | undefined;
}

function toEventList(value: SdkEvent | SdkEvent[] | null | undefined): SdkEvent[] {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  return [value];
}

function emitEvents(bus: SdkEventBus, value: SdkEvent | SdkEvent[] | null | undefined): void {
  const events = toEventList(value);
  for (const event of events) {
    bus.emit(event);
  }
}

export function createMethodSuccessEventMiddleware<M extends AsyncBackendMethodName>(
  options: MethodSuccessEventMiddlewareOptions<M>,
): BackendMiddleware {
  const { method, buildEvent } = options;

  return async (context, next) => {
    if (context.method !== method) {
      return next();
    }

    const result = await next();
    const typedContext = context as BackendCallContext<M>;
    const event = buildEvent({
      context: typedContext,
      args: typedContext.args,
      result: result as Awaited<ReturnType<AgentBackend[M]>>,
    });

    emitEvents(typedContext.bus, event);
    return result;
  };
}

function composeBackendMiddlewares(options: {
  context: BackendCallContext;
  middlewares: BackendMiddleware[];
  terminal: BackendCallNext;
}): Promise<unknown> {
  const { context, middlewares, terminal } = options;
  let index = -1;

  const dispatch = async (nextIndex: number): Promise<unknown> => {
    if (nextIndex <= index) {
      throw new Error('Backend middleware called next() multiple times');
    }

    index = nextIndex;
    const middleware = middlewares[nextIndex];
    if (!middleware) {
      return terminal();
    }

    return middleware(context, () => dispatch(nextIndex + 1));
  };

  return dispatch(0);
}

export function createEventedBackend(options: {
  backend: AgentBackend;
  scopeKey: string;
  bus: SdkEventBus;
  middlewares?: BackendMiddleware[];
}): AgentBackend {
  const { backend, scopeKey, bus } = options;
  const middlewares = options.middlewares ?? [];

  return new Proxy(backend, {
    get(target: AgentBackend, prop: string | symbol): any {
      const value = Reflect.get(target, prop, target);
      if (typeof value !== 'function' || typeof prop !== 'string') {
        return typeof value === 'function' ? value.bind(target) : value;
      }

      // `getCapabilities` is synchronous in the backend contract.
      if (prop === 'getCapabilities') {
        return value.bind(target);
      }

      return async (...args: any[]): Promise<unknown> => {
        const context: BackendCallContext = {
          method: prop as AsyncBackendMethodName,
          args: args as any,
          scopeKey,
          backend: target,
          bus,
          meta: {},
        };

        return composeBackendMiddlewares({
          context,
          middlewares,
          terminal: () => (value as UnknownAsyncFn).apply(target, args),
        });
      };
    },
  }) as AgentBackend;
}
