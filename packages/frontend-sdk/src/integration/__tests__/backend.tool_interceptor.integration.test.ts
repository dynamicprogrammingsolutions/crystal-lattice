import { afterAll, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import { ChatController } from '../../chat/chatController';
import { startBackendServer, waitForAsync } from '../harness';

function findRepoRoot(fromDir: string): string {
  let current = fromDir;
  for (let i = 0; i < 10; i += 1) {
    if (fs.existsSync(path.join(current, 'core', 'python'))) {
      return current;
    }
    const next = path.dirname(current);
    if (next === current) break;
    current = next;
  }
  throw new Error(`Unable to find repo root from ${fromDir}`);
}

function loadEnvVarFromRoot(name: string): string | null {
  const existing = process.env[name];
  if (typeof existing === 'string' && existing.trim()) {
    return existing.trim();
  }

  const candidates = new Set<string>();
  candidates.add(findRepoRoot(process.cwd()));
  try {
    const commonGitDir = execFileSync('git', ['rev-parse', '--git-common-dir'], {
      cwd: process.cwd(),
      encoding: 'utf8',
    }).trim();
    if (commonGitDir) {
      candidates.add(path.resolve(process.cwd(), commonGitDir, '..'));
    }
  } catch {
    // Fall back to the worktree-local repo root only.
  }

  for (const repoRoot of candidates) {
    const envPath = path.join(repoRoot, '.env');
    if (!fs.existsSync(envPath)) {
      continue;
    }

    const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) continue;
      const match = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
      if (!match || match[1] !== name) continue;
      let value = match[2].trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      if (value) {
        process.env[name] = value;
        return value;
      }
    }
  }

  return null;
}

const OPENROUTER_API_KEY = loadEnvVarFromRoot('OPENROUTER_API_KEY');
const OPENROUTER_BASE_URL = loadEnvVarFromRoot('OPENROUTER_BASE_URL');
const RUN =
  process.env.RUN_BACKEND_OPENROUTER_INTERCEPTOR_INTEGRATION === '1' &&
  !!OPENROUTER_API_KEY;
const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + frontend SDK + tool interception)', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  it('surfaces a pending tool prompt through the SDK and resumes the request after approval', async () => {
    const started = await startBackendServer({
      config: {
        plugin_cache_dir: '.plugin_cache',
        providers: {
          openrouter: {
            provider: 'openrouter',
            model: process.env.OPENROUTER_INTERCEPTOR_E2E_MODEL || 'openai/gpt-5.4-nano',
            api_key: OPENROUTER_API_KEY,
            base_url: OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
            timeout: 120,
          },
        },
        plugins: [
          'path:${env:REPO_ROOT}/plugins/openrouter',
          'path:${env:REPO_ROOT}/plugins/interceptor-tool',
        ],
        agents: { default: { provider: 'openrouter' } },
      },
      startupTimeoutMs: 120000,
    });
    stopServer = started.stop;

    const transport = new FetchTransport({ baseUrl: started.baseUrl });
    const backend = new RestAgentBackend({ transport });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;

    const controller = new ChatController({ backend, sessionId });
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
    controller.startEventStreaming({ initialSinceId: controller.getSnapshot().eventsCursorId });

    try {
      await controller.sendMessage({
        message: {
          role: 'user',
          content:
            'Use the add tool exactly once with a=2 and b=3. Do not answer from reasoning alone. After the tool result, reply with exactly INTERCEPT_OK_5.',
        },
        configOverrides: {},
      });

      const promptList = await (async () => {
        let prompts: Awaited<ReturnType<typeof backend.listSessionToolPrompts>> = [];
        await waitForAsync(async () => {
          prompts = await backend.listSessionToolPrompts(sessionId);
          return prompts.length > 0;
        }, { timeoutMs: 180000, intervalMs: 500 });
        return prompts;
      })();

      expect(promptList.length).toBeGreaterThan(0);
      const pending = promptList[0];
      expect(pending.tool_name).toBe('add');
      expect(String((pending.prompt as any)?.title || '')).toContain('Allow');

      const promptId = String((pending.prompt as any)?.id || '');
      expect(promptId).not.toBe('');

      const submitResult = await backend.submitSessionToolPromptResponse(
        sessionId,
        {
          prompt_id: promptId,
          button_id: 'allow',
          values: {},
        },
      );
      expect(submitResult.status).toBe('accepted');

      await waitForAsync(async () => {
        const listed = await backend.listMessages(sessionId);
        if (listed.activeRequestId != null) {
          return false;
        }
        const lastAssistant = [...listed.messages]
          .reverse()
          .find((message) => message.message.role === 'assistant');
        return lastAssistant?.message.content?.includes('INTERCEPT_OK_5') === true;
      }, { timeoutMs: 180000, intervalMs: 500 });

      const listed = await backend.listMessages(sessionId);
      const toolMessages = listed.messages.filter((message) => message.message.role === 'tool');
      expect(toolMessages.length).toBeGreaterThan(0);
      expect(toolMessages.some((message) => String(message.message.content || '').includes('Result: 5'))).toBe(true);

      const lastAssistant = [...listed.messages]
        .reverse()
        .find((message) => message.message.role === 'assistant');
      expect(String(lastAssistant?.message.content || '')).toContain('INTERCEPT_OK_5');
    } finally {
      controller.stopEventStreaming();
    }
  }, 360000);
});