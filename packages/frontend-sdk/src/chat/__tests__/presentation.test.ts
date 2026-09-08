import { describe, expect, it } from 'vitest';

import { deriveChatStatusBarParts } from '../presentation';

describe('deriveChatStatusBarParts', () => {
  it('includes the full session id', () => {
    const sessionId = 'session-1234567890abcdef';

    expect(
      deriveChatStatusBarParts({
        sessionId,
        lastAssistantMessage: null,
        statusBarElements: [],
      }),
    ).toContain(`Session: ${sessionId}`);
  });

  it('combines the active agent, UUID session id, and plugin total', () => {
    const sessionId = 'dc4efaec-9451-5981-a721-175a079860fb';

    expect(
      deriveChatStatusBarParts({
        sessionId,
        sessionAgentId: 'codex-openai',
        availableAgents: ['codex-openai'],
        lastAssistantMessage: {
          role: 'assistant',
          content: 'Done',
          metadata: {
            usage_total_cost_cumulative_formatted: '$0.013999',
          },
        },
        statusBarElements: [
          {
            ui_type: 'status_bar',
            data: 'metadata.usage_total_cost_cumulative_formatted',
            template: 'Total: {{data}}',
          },
        ],
      }),
    ).toEqual([
      'Agent: codex-openai',
      `Session: ${sessionId}`,
      'Total: $0.013999',
    ]);
  });
});