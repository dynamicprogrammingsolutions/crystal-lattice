import type { IndexedMessage } from '../types/messages';

export interface PendingToolPromptRow {
  messageIndex: number;
  phase: string | null;
  toolCallId: string | null;
  toolName: string | null;
  plugin: string | null;
  prompt: Record<string, any>;
}

function isNonEmptyButtons(prompt: Record<string, any>): boolean {
  const buttons = prompt.buttons;
  return Array.isArray(buttons) && buttons.some((b) => b && typeof b === 'object');
}

/**
 * Scan indexed messages for assistant rows with a pending tool interception prompt
 * (metadata.interception_current.pending_prompt with non-empty buttons).
 */
export function selectPendingToolPrompts(messages: IndexedMessage[]): PendingToolPromptRow[] {
  const out: PendingToolPromptRow[] = [];
  if (!Array.isArray(messages)) {
    return out;
  }
  for (const row of messages) {
    if (!row || row.message.role !== 'assistant') {
      continue;
    }
    const md = row.message.metadata;
    if (!md || typeof md !== 'object') {
      continue;
    }
    const current = (md as Record<string, any>).interception_current;
    if (!current || typeof current !== 'object') {
      continue;
    }
    const pending = (current as Record<string, any>).pending_prompt;
    if (!pending || typeof pending !== 'object') {
      continue;
    }
    const prompt = pending as Record<string, any>;
    if (!isNonEmptyButtons(prompt)) {
      continue;
    }
    const phase =
      typeof (current as Record<string, any>).phase === 'string'
        ? ((current as Record<string, any>).phase as string)
        : null;
    const toolCallId =
      typeof (current as Record<string, any>).tool_call_id === 'string'
        ? ((current as Record<string, any>).tool_call_id as string)
        : null;
    const toolName =
      typeof (current as Record<string, any>).tool_name === 'string'
        ? ((current as Record<string, any>).tool_name as string)
        : null;
    const plugin =
      typeof (current as Record<string, any>).plugin === 'string'
        ? ((current as Record<string, any>).plugin as string)
        : null;
    out.push({
      messageIndex: row.index,
      phase,
      toolCallId,
      toolName,
      plugin,
      prompt,
    });
  }
  return out;
}
