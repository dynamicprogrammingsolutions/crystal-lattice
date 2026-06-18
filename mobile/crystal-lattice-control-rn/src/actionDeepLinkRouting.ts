import {
  parseActionDeepLink,
  type AgentBackend,
  type ExecuteActionResponse,
  type ExecuteActionResponseOk,
  type ParsedActionDeepLink,
} from '@crystal-lattice/frontend-sdk';

export type ActionDeepLinkRoutingResult =
  | { handled: false }
  | { handled: true; status: 'queued'; parsed: ParsedActionDeepLink }
  | {
      handled: true;
      status: 'ok';
      parsed: ParsedActionDeepLink;
      response: ExecuteActionResponseOk;
    }
  | {
      handled: true;
      status: 'error';
      parsed?: ParsedActionDeepLink;
      errorType: string;
      message: string;
      response?: ExecuteActionResponse;
    };

export interface ActionDeepLinkHandlerOptions {
  hasConnection: (connectionId: string) => boolean;
  getBackendForConnection: (connectionId: string) => AgentBackend | null;
  queuePendingAction?: (parsed: ParsedActionDeepLink) => void;
}

export function createActionDeepLinkHandler(options: ActionDeepLinkHandlerOptions) {
  return async function handleIncomingUrl(
    url: string | null | undefined,
  ): Promise<ActionDeepLinkRoutingResult> {
    if (!url) {
      return { handled: false };
    }

    const parsed = parseActionDeepLink(url);
    if (!parsed) {
      return { handled: false };
    }

    if (!options.hasConnection(parsed.connectionId)) {
      return {
        handled: true,
        status: 'error',
        parsed,
        errorType: 'unknown_connection',
        message: `Unknown connection ${parsed.connectionId}`,
      };
    }

    const backend = options.getBackendForConnection(parsed.connectionId);
    if (!backend) {
      options.queuePendingAction?.(parsed);
      return {
        handled: true,
        status: 'queued',
        parsed,
      };
    }

    if (typeof backend.executeSessionAction !== 'function') {
      return {
        handled: true,
        status: 'error',
        parsed,
        errorType: 'unsupported_backend',
        message: 'Backend does not support session actions',
      };
    }

    try {
      const response = await backend.executeSessionAction({
        sessionId: parsed.sessionId,
        pluginId: parsed.pluginId,
        actionId: parsed.actionId,
        inputs: parsed.inputs,
      });

      if (!response || response.status !== 'ok') {
        return {
          handled: true,
          status: 'error',
          parsed,
          errorType: response?.error_type || 'action_failed',
          message:
            response?.message ||
            (response?.error_type ? `Action failed: ${response.error_type}` : 'Action failed'),
          response,
        };
      }

      return {
        handled: true,
        status: 'ok',
        parsed,
        response,
      };
    } catch (error: any) {
      return {
        handled: true,
        status: 'error',
        parsed,
        errorType: 'exception',
        message: error?.message || 'Action failed',
      };
    }
  };
}