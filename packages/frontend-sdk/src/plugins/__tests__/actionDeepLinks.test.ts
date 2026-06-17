import { describe, expect, it } from 'vitest';

import { parseActionDeepLink } from '../actionDeepLinks';

describe('parseActionDeepLink', () => {
  it('parses plugin-qualified session action links', () => {
    expect(
      parseActionDeepLink(
        'crystal-lattice://action/test-connection/session-123/generic_callback_app/complete_external_flow?result=approved&nonce=n-123',
      ),
    ).toEqual({
      connectionId: 'test-connection',
      sessionId: 'session-123',
      pluginId: 'generic_callback_app',
      actionId: 'complete_external_flow',
      inputs: {
        result: 'approved',
        nonce: 'n-123',
        redirect_url:
          'crystal-lattice://action/test-connection/session-123/generic_callback_app/complete_external_flow?result=approved&nonce=n-123',
      },
      redirectUrl:
        'crystal-lattice://action/test-connection/session-123/generic_callback_app/complete_external_flow?result=approved&nonce=n-123',
    });
  });

  it('parses session action links without plugin ids', () => {
    expect(
      parseActionDeepLink(
        'crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved',
      ),
    ).toEqual({
      connectionId: 'test-connection',
      sessionId: 'session-123',
      actionId: 'complete_external_flow',
      inputs: {
        result: 'approved',
        redirect_url:
          'crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved',
      },
      redirectUrl:
        'crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved',
    });
  });

  it('rejects malformed or unrelated routes', () => {
    expect(parseActionDeepLink('https://example.com/action/a')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://settings/a')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://action')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://action/connection-only')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://action/connection/session')).toBeNull();
    expect(
      parseActionDeepLink('crystal-lattice://action/a/b/c/d/e'),
    ).toBeNull();
    expect(parseActionDeepLink('not a url')).toBeNull();
  });
});