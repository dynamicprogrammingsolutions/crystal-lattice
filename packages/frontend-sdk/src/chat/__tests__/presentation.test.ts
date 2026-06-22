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
});