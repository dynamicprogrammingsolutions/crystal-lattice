import type { AgentBackend } from '../backend/backend';
import type { SdkEventBus } from '../runtime/sdkEventBus';
import type { BackendMiddleware } from '../runtime/eventedBackend';
import { SdkRuntime } from '../runtime/sdkRuntime';
import { createDefaultBackendMiddlewares } from './createDefaultBackendMiddlewares';

export interface CreateDefaultSdkRuntimeOptions {
  scopeKey: string;
  backend?: AgentBackend | null;
  bus?: SdkEventBus;
  extraBackendMiddlewares?: BackendMiddleware[];
}

export function createDefaultSdkRuntime(options: CreateDefaultSdkRuntimeOptions): SdkRuntime {
  return new SdkRuntime({
    scopeKey: options.scopeKey,
    backend: options.backend,
    bus: options.bus,
    backendMiddlewares: createDefaultBackendMiddlewares({
      extraBackendMiddlewares: options.extraBackendMiddlewares,
    }),
  });
}
