import http from 'node:http';
import { URLSearchParams } from 'node:url';

import { getFreePort } from './harness';

export interface McpAuthFixture {
  baseUrl: string;
  mcpUrl: string;
  authorizeUrl: string;
  tokenUrl: string;
  mcpAuthorizationHeaders: string[];
  tokenRequests: Array<Record<string, string>>;
  stop: () => Promise<void>;
}

async function readBody(req: http.IncomingMessage): Promise<string> {
  return await new Promise((resolve, reject) => {
    let body = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => {
      body += chunk;
    });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

export async function startMcpAuthFixture(): Promise<McpAuthFixture> {
  const port = await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const mcpAuthorizationHeaders: string[] = [];
  const tokenRequests: Array<Record<string, string>> = [];

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url || '/', baseUrl);
    if (url.pathname === '/mcp') {
      const authorization = req.headers.authorization;
      if (typeof authorization === 'string') {
        mcpAuthorizationHeaders.push(authorization);
      }
      res.statusCode = 401;
      res.setHeader(
        'WWW-Authenticate',
        `Bearer resource_metadata="${baseUrl}/.well-known/oauth-protected-resource"`,
      );
      res.end('Authentication required');
      return;
    }

    if (url.pathname === '/.well-known/oauth-protected-resource') {
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          resource: `${baseUrl}/mcp`,
          authorization_servers: [baseUrl],
        }),
      );
      return;
    }

    if (url.pathname === '/token' && req.method === 'POST') {
      const params = new URLSearchParams(await readBody(req));
      const captured: Record<string, string> = {};
      for (const [key, value] of params.entries()) {
        captured[key] = value;
      }
      tokenRequests.push(captured);
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          access_token: 'access-123',
          token_type: 'Bearer',
          expires_in: 3600,
        }),
      );
      return;
    }

    if (url.pathname === '/authorize') {
      res.statusCode = 200;
      res.end('authorization page');
      return;
    }

    res.statusCode = 404;
    res.end('not found');
  });

  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => {
      server.off('error', reject);
      resolve();
    });
  });

  return {
    baseUrl,
    mcpUrl: `${baseUrl}/mcp`,
    authorizeUrl: `${baseUrl}/authorize`,
    tokenUrl: `${baseUrl}/token`,
    mcpAuthorizationHeaders,
    tokenRequests,
    stop: async () => {
      await new Promise<void>((resolve) => server.close(() => resolve()));
    },
  };
}