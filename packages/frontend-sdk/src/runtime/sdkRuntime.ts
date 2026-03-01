import type { AgentBackend } from '../backend/backend';
import { createEventedBackend, type BackendMiddleware } from './eventedBackend';
import { SdkEventBus } from './sdkEventBus';

export interface SdkRuntimeOptions {
  scopeKey: string;
  backend?: AgentBackend | null;
  bus?: SdkEventBus;
  backendMiddlewares?: BackendMiddleware[];
}

export class SdkRuntime {
  readonly scopeKey: string;
  readonly bus: SdkEventBus;
  readonly rawBackend: AgentBackend | null;
  readonly backend: AgentBackend | null;

  constructor(options: SdkRuntimeOptions) {
    this.scopeKey = options.scopeKey;
    this.bus = options.bus ?? new SdkEventBus();
    this.rawBackend = options.backend ?? null;
    this.backend = this.rawBackend
      ? createEventedBackend({
          backend: this.rawBackend,
          scopeKey: this.scopeKey,
          bus: this.bus,
          middlewares: options.backendMiddlewares,
        })
      : null;
  }
}
