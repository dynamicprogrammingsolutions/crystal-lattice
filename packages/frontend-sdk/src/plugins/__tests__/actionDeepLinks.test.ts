import { describe, expect, it } from 'vitest';

import { parseActionDeepLink } from '../actionDeepLinks';

describe('parseActionDeepLink', () => {
  it('parses plugin-qualified action links', () => {
    expect(
      parseActionDeepLink(
        'crystal-lattice://action/mcp_runtime_app/mcp_complete_login?code=a&state=b',
      ),
    ).toEqual({
      pluginId: 'mcp_runtime_app',
      actionId: 'mcp_complete_login',
      inputs: {
        code: 'a',
        state: 'b',
        redirect_url:
          'crystal-lattice://action/mcp_runtime_app/mcp_complete_login?code=a&state=b',
      },
      redirectUrl:
        'crystal-lattice://action/mcp_runtime_app/mcp_complete_login?code=a&state=b',
    });
  });

  it('parses action links without plugin ids', () => {
    expect(parseActionDeepLink('crystal-lattice://action/mcp_complete_login?code=a')).toEqual({
      actionId: 'mcp_complete_login',
      inputs: {
        code: 'a',
        redirect_url: 'crystal-lattice://action/mcp_complete_login?code=a',
      },
      redirectUrl: 'crystal-lattice://action/mcp_complete_login?code=a',
    });
  });

  it('rejects malformed or unrelated routes', () => {
    expect(parseActionDeepLink('https://example.com/action/a')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://settings/a')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://action')).toBeNull();
    expect(parseActionDeepLink('crystal-lattice://action/a/b/c')).toBeNull();
    expect(parseActionDeepLink('not a url')).toBeNull();
  });
});