export interface PendingSendMessageRecovery {
  kind: 'send_message';
  idempotencyKey: string;
  requestedAtMs: number;
  errorMessage: string;
  message: {
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    multipartContent?: any[] | null;
    metadata?: Record<string, any>;
  };
  configOverrides?: Record<string, any>;
}

export interface PendingResendRecovery {
  kind: 'send';
  idempotencyKey: string;
  requestedAtMs: number;
  errorMessage: string;
  configOverrides?: Record<string, any>;
}

export type PendingRequestRecovery = PendingSendMessageRecovery | PendingResendRecovery;

export function describePendingRequestRecovery(pending: PendingRequestRecovery): string {
  if (pending.kind === 'send_message') {
    const content = pending.message.content.trim();
    if (content) {
      return content.length > 72 ? `${content.slice(0, 69)}...` : content;
    }
    const partCount = Array.isArray(pending.message.multipartContent)
      ? pending.message.multipartContent.length
      : 0;
    return partCount > 0
      ? `Multipart message (${partCount} part${partCount === 1 ? '' : 's'})`
      : 'Message send';
  }

  return 'Resend request';
}

export function shouldClearPendingRequestRecovery(options: {
  pending: PendingRequestRecovery | null;
  activeRequestId: string | null;
}): boolean {
  return !!options.pending && !!options.activeRequestId;
}