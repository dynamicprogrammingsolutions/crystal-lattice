import type { BackendMiddleware } from '../runtime/eventedBackend';
import { createDefaultSessionMutationMiddlewares } from '../sessionMutations/sessionMutationMiddlewares';

export interface CreateDefaultBackendMiddlewaresOptions {
  extraBackendMiddlewares?: BackendMiddleware[];
}

export function createDefaultBackendMiddlewares(
  options: CreateDefaultBackendMiddlewaresOptions = {},
): BackendMiddleware[] {
  return [
    ...createDefaultSessionMutationMiddlewares(),
    ...(options.extraBackendMiddlewares ?? []),
  ];
}
