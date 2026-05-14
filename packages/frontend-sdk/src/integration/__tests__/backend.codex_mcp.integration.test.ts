import { afterAll, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
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

  const repoRoot = findRepoRoot(process.cwd());
  const envPath = path.join(repoRoot, '.env');
  if (!fs.existsSync(envPath)) {
    return null;
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

  return null;
}

function commandExists(command: string, args: string[] = ['--version']): boolean {
  try {
    execFileSync(command, args, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function extractDisplayBody(response: any): string {
  const body = response?.result?.display?.body;
  return typeof body === 'string' ? body : '';
}

const OPENROUTER_API_KEY = loadEnvVarFromRoot('OPENROUTER_API_KEY');
const OPENROUTER_BASE_URL = loadEnvVarFromRoot('OPENROUTER_BASE_URL');
const TEST_MODEL = 'openai/gpt-5.4-nano';
const RUN =
  process.env.RUN_BACKEND_OPENROUTER_INTEGRATION === '1' &&
  !!OPENROUTER_API_KEY &&
  commandExists('npx');
const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + frontend SDK + Codex MCP)', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  it('enables MCP through SDK-discovered UI schema and exercises MCP app actions through the SDK', async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const workspaceRoot = path.join(repoRoot, '.tmp-mcp-sdk-e2e');
    fs.mkdirSync(workspaceRoot, { recursive: true });
    const workspaceDir = fs.mkdtempSync(path.join(workspaceRoot, 'codex-mcp-sdk-'));
    const targetPath = path.join(workspaceDir, 'note.txt');
    fs.writeFileSync(targetPath, 'alpha from mcp\nsecond line\n', 'utf8');

    const started = await startBackendServer({
      config: {
        plugin_cache_dir: '.plugin_cache',
        providers: {
          openrouter: {
            provider: 'openrouter',
            model: 'openai/gpt-5.4-mini',
            api_key: OPENROUTER_API_KEY,
            base_url: OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
            timeout: 120,
          },
        },
        plugins: [
          'path:${env:REPO_ROOT}/plugins/openrouter',
          'path:${env:REPO_ROOT}/plugins/mcp-runtime-app',
        ],
        agents: {
          'codex-openrouter': {
            provider: 'openrouter',
            model: 'openai/gpt-5.4-mini',
            plugins: ['path:${env:REPO_ROOT}/plugins/codex-tools'],
            shell_tool_mode: 'auto',
            mcp_enabled: false,
            mcp_reuse_runtime: true,
            mcp_fail_on_startup_error: false,
            mcp_servers: {
              filesystem: {
                enabled: false,
                transport: 'stdio',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-filesystem', workspaceDir],
                cwd: workspaceDir,
                startup_timeout_seconds: 30,
                tool_timeout_seconds: 30,
              },
            },
          },
        },
      },
      startupTimeoutMs: 120000,
    });
    stopServer = started.stop;

    const transport = new FetchTransport({ baseUrl: started.baseUrl });
    const backend = new RestAgentBackend({ transport });

    try {
      const created = await backend.createSession({ agentId: 'codex-openrouter' });
      const sessionId = created.session.session_id;

      const plugins = await backend.listSessionPlugins(sessionId);
      const enabledPluginIds = plugins
        .filter((entry) => {
          if (!entry || entry.enabled !== true) {
            return false;
          }
          return entry.kind !== 'tools' || entry.id === 'codex_mcp_tool';
        })
        .map((entry) => entry.id);
      expect(enabledPluginIds).toContain('codex_mcp_tool');

      await backend.setSessionPlugins(sessionId, enabledPluginIds);
      const updatedPlugins = await backend.listSessionPlugins(sessionId);
      expect(
        updatedPlugins.some((entry) => entry.id === 'codex_mcp_tool' && entry.enabled === true),
      ).toBe(true);
      expect(
        updatedPlugins
          .filter((entry) => entry.kind === 'tools' && ['shell', 'shell_command'].includes(entry.id))
          .every((entry) => entry.enabled === false),
      ).toBe(true);

      const uiElements = await backend.getSessionUiSchema(sessionId);
      const globalToggle = uiElements.find((element) => element?.key === 'mcp_enabled');
      const serverToggle = uiElements.find(
        (element) =>
          typeof element?.key === 'string' &&
          String(element.key).startsWith('mcp_server__'),
      );
      expect(globalToggle?.type).toBe('checkbox');
      expect(serverToggle?.type).toBe('checkbox');

      const configSchema = await backend.getSessionConfigSchema(sessionId);
      expect(configSchema.some((entry) => entry?.key === 'model')).toBe(true);

      await backend.patchSessionOverrides(sessionId, {
        model: TEST_MODEL,
        mcp_enabled: true,
        [String(serverToggle?.key)]: true,
      });

      const appUi = await backend.getSessionApplicationUiSchema(sessionId);
      const statusAction = appUi.find(
        (element: any) =>
          element?.plugin === 'mcp_runtime_app' &&
          element?.action_id === 'mcp_show_status',
      ) as any;
      expect(statusAction).toBeTruthy();

      const statusBefore = await backend.executeAction({
        pluginId: 'mcp_runtime_app',
        actionId: 'mcp_show_status',
        inputs: { session_id: sessionId },
      });
      expect(statusBefore.status).toBe('ok');
      expect(extractDisplayBody(statusBefore)).toContain(
        'No MCP runtimes are currently stored.',
      );

      await backend.sendMessage(sessionId, {
        message: {
          role: 'user',
          content:
            'Use an MCP filesystem tool to read the file at ' +
            `${targetPath} and then answer with exactly the first line of that file and nothing else.`,
        },
        configOverrides: {},
      });

      await waitForAsync(async () => {
        const listed = await backend.listMessages(sessionId);
        if (listed.activeRequestId != null) {
          return false;
        }
        const lastAssistant = [...listed.messages]
          .reverse()
          .find((message) => message.message.role === 'assistant');
        return lastAssistant?.message.content === 'alpha from mcp';
      }, { timeoutMs: 240000, intervalMs: 250 });

      const listed = await backend.listMessages(sessionId);
      const toolMessages = listed.messages.filter((message) => message.message.role === 'tool');
      expect(toolMessages.length).toBeGreaterThan(0);
      expect(
        toolMessages.some((message: any) =>
          String(message.message?.metadata?.tool_name || '').startsWith('mcp__filesystem__'),
        ),
      ).toBe(true);

      const lastAssistant = [...listed.messages]
        .reverse()
        .find((message) => message.message.role === 'assistant');
      expect(lastAssistant?.message.content).toBe('alpha from mcp');

      const statusAfter = await backend.executeAction({
        pluginId: 'mcp_runtime_app',
        actionId: 'mcp_show_status',
        inputs: { session_id: sessionId },
      });
      expect(statusAfter.status).toBe('ok');
      expect(extractDisplayBody(statusAfter)).toContain('filesystem');
      expect(extractDisplayBody(statusAfter)).toContain('connected');

    } finally {
      if (stopServer) {
        await stopServer();
        stopServer = null;
      }
      fs.rmSync(workspaceDir, { recursive: true, force: true });
    }
  }, 360000);
});