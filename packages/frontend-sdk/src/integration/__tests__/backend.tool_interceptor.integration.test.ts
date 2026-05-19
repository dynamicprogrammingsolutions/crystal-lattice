import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import { ChatController } from '../../chat/chatController';
import { startBackendServer, waitForAsync, type StartedServer } from '../harness';
import { selectPendingToolPrompts } from '../../toolInterceptor/selectPendingToolPrompts';

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
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
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
const OPENAI_API_KEY = loadEnvVarFromRoot('OPENAI_API_KEY');
const RUN =
  process.env.RUN_BACKEND_OPENROUTER_INTERCEPTOR_INTEGRATION === '1' &&
  (!!OPENROUTER_API_KEY || !!OPENAI_API_KEY);
const describeIf = RUN ? describe : describe.skip;

type ProviderCase = {
  agentId: 'intercept-openrouter' | 'intercept-openai';
  providerName: 'openrouter' | 'openai';
  requiredKey: string | null;
};

const CASES: ProviderCase[] = [
  {
    agentId: 'intercept-openrouter',
    providerName: 'openrouter',
    requiredKey: OPENROUTER_API_KEY,
  },
  {
    agentId: 'intercept-openai',
    providerName: 'openai',
    requiredKey: OPENAI_API_KEY,
  },
];

describeIf('backend integration (real FastAPI server + frontend SDK + tool interception provider matrix)', () => {
  let started: StartedServer | null = null;

  beforeAll(async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const configPath = path.join(
      repoRoot,
      'packages',
      'frontend-sdk',
      'src',
      'integration',
      'fixtures',
      'interceptor-provider-matrix.config.json',
    );
    started = await startBackendServer({
      config: {},
      configPath,
      startupTimeoutMs: 120000,
    });
  }, 180000);

  afterAll(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  async function waitForCompletedInterceptedSession(options: {
    backend: RestAgentBackend;
    controller: ChatController;
    sessionId: string;
  }): Promise<void> {
    try {
      await waitForAsync(async () => {
        const listed = await options.backend.listMessages(options.sessionId);
        if (listed.activeRequestId != null) {
          return false;
        }
        const toolMessages = listed.messages.filter((message) => message.message.role === 'tool');
        const lastAssistant = [...listed.messages]
          .reverse()
          .find((message) => message.message.role === 'assistant');
        return (
          toolMessages.some((message) => String(message.message.content || '').includes('Result: 5')) &&
          String(lastAssistant?.message.content || '').includes('INTERCEPT_OK_5')
        );
      }, { timeoutMs: 180000, intervalMs: 500 });
    } catch (err) {
      const listed = await options.backend.listMessages(options.sessionId);
      const prompts = await options.backend.listSessionToolPrompts(options.sessionId);
      const snapshot = options.controller.getSnapshot();
      const toolMessages = listed.messages
        .filter((message) => message.message.role === 'tool')
        .map((message) => String(message.message.content || ''));
      const lastAssistant = [...listed.messages]
        .reverse()
        .find((message) => message.message.role === 'assistant');
      const promptSummary = prompts.map((prompt) => ({
        message_index: prompt.message_index,
        phase: prompt.phase,
        tool_call_id: prompt.tool_call_id,
        tool_name: prompt.tool_name,
        prompt_id: (prompt.prompt as any)?.id ?? null,
        title: (prompt.prompt as any)?.title ?? null,
      }));
      throw new Error(
        [
          err instanceof Error ? err.message : String(err),
          `activeRequestId=${String(listed.activeRequestId)}`,
          `toolMessages=${JSON.stringify(toolMessages)}`,
          `lastAssistant=${JSON.stringify(String(lastAssistant?.message.content || ''))}`,
          `pendingPrompts=${JSON.stringify(promptSummary)}`,
          `controllerDirty=${String(snapshot.dirty)}`,
          `controllerDirtyReason=${String(snapshot.dirtyReason)}`,
          `controllerPromptRows=${JSON.stringify(
            selectPendingToolPrompts(snapshot.messages).map((row) => ({
              messageIndex: row.messageIndex,
              phase: row.phase,
              toolCallId: row.toolCallId,
              toolName: row.toolName,
              promptId: (row.prompt as any)?.id ?? null,
              title: (row.prompt as any)?.title ?? null,
            })),
          )}`,
        ].join('\n'),
      );
    }

    await options.controller.loadMessages();
  }

  async function runHappyPathCase(providerCase: ProviderCase): Promise<void> {
    if (!started) {
      throw new Error('backend server was not started');
    }

    const transport = new FetchTransport({ baseUrl: started.baseUrl });
    const backend = new RestAgentBackend({ transport });
    const created = await backend.createSession({ agentId: providerCase.agentId });
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

      expect(promptList.length, `${providerCase.providerName} should surface an interceptor prompt`).toBeGreaterThan(0);
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

      await waitForCompletedInterceptedSession({ backend, controller, sessionId });

      const listedAfterCompletion = await backend.listMessages(sessionId);
      const toolMessagesAfterCompletion = listedAfterCompletion.messages.filter(
        (message) => message.message.role === 'tool',
      );
      expect(toolMessagesAfterCompletion.length).toBeGreaterThan(0);
      expect(
        toolMessagesAfterCompletion.some((message) => String(message.message.content || '').includes('Result: 5')),
      ).toBe(true);

      const lastAssistantAfterCompletion = [...listedAfterCompletion.messages]
        .reverse()
        .find((message) => message.message.role === 'assistant');
      expect(String(lastAssistantAfterCompletion?.message.content || '')).toContain('INTERCEPT_OK_5');

      const promptsAfterCompletion = await backend.listSessionToolPrompts(sessionId);
      expect(promptsAfterCompletion).toEqual([]);
      expect(selectPendingToolPrompts(controller.getSnapshot().messages)).toEqual([]);

      const reopenedController = new ChatController({ backend, sessionId });
      try {
        await reopenedController.loadMessagesFromRangeText({ startText: '-50', endText: '' });

        const reopenedSnapshot = reopenedController.getSnapshot();
        const reopenedToolMessages = reopenedSnapshot.messages.filter(
          (row) => row.message.role === 'tool',
        );
        expect(reopenedToolMessages.length).toBeGreaterThan(0);
        expect(
          reopenedToolMessages.some((row) => String(row.message.content || '').includes('Result: 5')),
        ).toBe(true);

        const reopenedLastAssistant = [...reopenedSnapshot.messages]
          .reverse()
          .find((row) => row.message.role === 'assistant');
        expect(String(reopenedLastAssistant?.message.content || '')).toContain('INTERCEPT_OK_5');
        expect(selectPendingToolPrompts(reopenedSnapshot.messages)).toEqual([]);
      } finally {
        reopenedController.stopEventStreaming();
      }
    } finally {
      controller.stopEventStreaming();
    }
  }

  for (const providerCase of CASES) {
    const itCase = providerCase.requiredKey ? it : it.skip;
    itCase(
      `completes the full interceptor happy path with ${providerCase.providerName}`,
      async () => {
        await runHappyPathCase(providerCase);
      },
      360000,
    );
  }
});