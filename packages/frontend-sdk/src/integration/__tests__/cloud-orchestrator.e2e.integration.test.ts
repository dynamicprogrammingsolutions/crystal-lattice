import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import {
  CloudTransport,
  parseCloudConnectionLink,
} from '../../transport/cloudTransport';
import {
  type StartedCloudOrchestrator,
  startBackendServer,
  startCloudOrchestratorForE2E,
  waitForAsync,
} from '../harness';

const CLOUD_ORCHESTRATOR_E2E_MODE = process.env.CLOUD_ORCHESTRATOR_E2E_MODE || '';
const IS_LOCAL_CLOUD_ORCHESTRATOR_E2E =
  CLOUD_ORCHESTRATOR_E2E_MODE === '' || CLOUD_ORCHESTRATOR_E2E_MODE === 'local';
const IS_AWS_E2E = CLOUD_ORCHESTRATOR_E2E_MODE.startsWith('aws-');
// Keep provider-gated suites gated only by explicit test flags. The backend
// application loads dotenv values from the config directory, .crystal dirs, and
// the current directory/parents; checking provider keys in this Node process
// would skip before exercising the normal application credential path.
const RUN_OPENROUTER =
  process.env.RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E === '1';
const describeOpenRouterIf = RUN_OPENROUTER ? describe : describe.skip;
const RUN_CODEX_DEFAULT_CONFIG =
  process.env.RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E === '1';
const describeCodexDefaultConfigIf = RUN_CODEX_DEFAULT_CONFIG ? describe.sequential : describe.skip;
const RUN_CODEX_DEFAULT_CONFIG_EC2 =
  process.env.RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E === '1' &&
  CLOUD_ORCHESTRATOR_E2E_MODE === 'aws-ec2-cloudfront';
const describeCodexDefaultConfigEc2If = RUN_CODEX_DEFAULT_CONFIG_EC2
  ? describe.sequential
  : describe.skip;

const TEST_TIMEOUT_MS = IS_AWS_E2E ? 2_700_000 : 600_000;
const HOOK_TIMEOUT_MS = IS_AWS_E2E ? 900_000 : 60_000;
const CODEX_DEFAULT_CONFIG_HOOK_TIMEOUT_MS = Math.max(HOOK_TIMEOUT_MS, 180_000);

function localBackendConfig(options: {
  orchestratorUrl: string;
  workspaceDir: string;
}) {
  const cloudAgent: Record<string, any> = {
    orchestrator_url: options.orchestratorUrl,
    workspace_dir: options.workspaceDir,
    transfer_method: 'managed_ssh',
    project_config_path: '${env:WORKING_DIR}/.cloud-agent/cloud-agent.json',
    config_assets: {
      include_config_dir: true,
      exclude: ['.env'],
      max_top_level_entry_bytes: 100,
    },
    runtime_env: {
      include_config_env: true,
      include: [],
      exclude: [
        'CLOUD_ORCHESTRATOR_URL',
        'CLOUD_ORCHESTRATOR_TOKEN',
        'CONFIG_DIR',
        'BUILTIN_PLUGINS',
      ],
      env_files: [],
    },
  };
  if (process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN) {
    cloudAgent.orchestrator_token = process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN;
  }

  return {
    providers: {
      test_provider: {
        provider: 'echo_openai_like',
        model: 'test-model',
        timeout: 60,
        stream: false,
        working_directory: '${env:WORKING_DIR}',
        allowed_paths: ['${env:WORKING_DIR}'],
      },
    },
    plugins: [
      'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
      'plugins.file_writer_tool.FileWriterTool',
      'path:${env:BUILTIN_PLUGINS}/session-title-app',
      'path:${env:BUILTIN_PLUGINS}/cloud-agent-app',
    ],
    agents: {
      default: {
        provider: 'test_provider',
      },
    },
    application: {
      cloud_agent: cloudAgent,
    },
  };
}

function openRouterBackendConfig(options: {
  orchestratorUrl: string;
  workspaceDir: string;
}) {
  const model = process.env.CLOUD_ORCHESTRATOR_OPENROUTER_MODEL || 'openai/gpt-4.1-mini';
  const cloudAgent: Record<string, any> = {
    orchestrator_url: options.orchestratorUrl,
    workspace_dir: options.workspaceDir,
    transfer_method: 'managed_ssh',
    project_config_path: '${env:WORKING_DIR}/.cloud-agent/cloud-agent.json',
    config_assets: {
      include_config_dir: true,
      exclude: ['.env'],
      max_top_level_entry_bytes: 1_000_000,
    },
    runtime_env: {
      include_config_env: true,
      include: [],
      exclude: [
        'CLOUD_ORCHESTRATOR_URL',
        'CLOUD_ORCHESTRATOR_TOKEN',
        'CONFIG_DIR',
        'BUILTIN_PLUGINS',
      ],
      env_files: [],
    },
  };
  if (process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN) {
    cloudAgent.orchestrator_token = process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN;
  }

  return {
    providers: {
      openrouter: {
        provider: 'openrouter',
        api_key: '${env:OPENROUTER_API_KEY}',
        base_url: 'https://openrouter.ai/api/v1',
        model,
        timeout: 120,
        working_directory: '${env:WORKING_DIR}',
        allowed_paths: ['${env:WORKING_DIR}'],
        system_message_enabled: true,
        system_message: {
          template: '${file:${env:CONFIG_DIR}/system_messages/openrouter-e2e.md}',
        },
      },
    },
    plugins: [
      'path:${env:BUILTIN_PLUGINS}/openrouter',
      'path:${env:BUILTIN_PLUGINS}/feature-system-message',
      'plugins.file_writer_tool.FileWriterTool',
      'path:${env:BUILTIN_PLUGINS}/cloud-agent-app',
    ],
    agents: {
      default: {
        provider: 'openrouter',
      },
    },
    application: {
      cloud_agent: cloudAgent,
    },
  };
}

function writeCloudAgentScripts(workspaceDir: string): void {
  const scriptsDir = path.join(workspaceDir, '.cloud-agent');
  fs.mkdirSync(scriptsDir, { recursive: true });
  const repoRoot = findRepoRoot(process.cwd());

  const scripts: Record<string, string> = {
    'transfer-up': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${LOCAL_WORKSPACE_DIR:?}"',
      ': "${TRANSFER_DIR:?}"',
      'cd "${LOCAL_WORKSPACE_DIR}"',
      'payload_dir="${TRANSFER_DIR}/.cloud-agent"',
      'mkdir -p "${payload_dir}"',
      'git rev-parse --show-toplevel >/dev/null',
      'git archive --format=tar --output="${payload_dir}/project.tar" HEAD',
      'index_file="${payload_dir}/transfer.index"',
      'rm -f "${index_file}"',
      'GIT_INDEX_FILE="${index_file}" git read-tree HEAD',
      'GIT_INDEX_FILE="${index_file}" git add -A -- . \':(exclude).cloud-agent\'',
      'GIT_INDEX_FILE="${index_file}" git diff --cached --binary HEAD > "${payload_dir}/working.patch"',
      'rm -f "${index_file}"',
    ].join('\n'),
    'setup-cloud': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${CLOUD_WORKSPACE_DIR:?}"',
      ': "${TRANSFER_DIR:?}"',
      'payload_dir="${TRANSFER_DIR}/.cloud-agent"',
      'archive_path="${payload_dir}/project.tar"',
      'patch_path="${payload_dir}/working.patch"',
      'mkdir -p "${CLOUD_WORKSPACE_DIR}"',
      'tar -xf "${archive_path}" -C "${CLOUD_WORKSPACE_DIR}"',
      'cd "${CLOUD_WORKSPACE_DIR}"',
      'git init -q',
      'git add -A',
      'git -c user.name=\'Cloud Agent\' -c user.email=\'cloud-agent@example.invalid\' commit -q -m \'cloud-agent baseline\'',
      'if [ -s "${patch_path}" ]; then',
      '  git apply --binary "${patch_path}"',
      '  git add -A',
      '  git -c user.name=\'Cloud Agent\' -c user.email=\'cloud-agent@example.invalid\' commit -q -m \'cloud-agent local input\'',
      'fi',
    ].join('\n'),
    'export-cloud': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${CLOUD_WORKSPACE_DIR:?}"',
      ': "${TRANSFER_DIR:?}"',
      'payload_dir="${TRANSFER_DIR}/.cloud-agent"',
      'mkdir -p "${payload_dir}"',
      'cd "${CLOUD_WORKSPACE_DIR}"',
      'git add -A',
      'git diff --cached --binary HEAD > "${payload_dir}/cloud.patch"',
    ].join('\n'),
    'apply-down': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${LOCAL_WORKSPACE_DIR:?}"',
      ': "${TRANSFER_DIR:?}"',
      'patch_path="${TRANSFER_DIR}/.cloud-agent/cloud.patch"',
      'cd "${LOCAL_WORKSPACE_DIR}"',
      'if [ -s "${patch_path}" ]; then',
      '  if git apply --check --binary "${patch_path}" >/dev/null 2>&1; then',
      '    git apply --binary "${patch_path}"',
      '  elif git apply --reverse --check --binary "${patch_path}" >/dev/null 2>&1; then',
      '    exit 0',
      '  else',
      '    git apply --check --binary "${patch_path}"',
      '  fi',
      'fi',
    ].join('\n'),
    'install-cloud': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      'exit 0',
    ].join('\n'),
    'validate-cloud': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${CLOUD_WORKSPACE_DIR:?}"',
      'test -d "${CLOUD_WORKSPACE_DIR}"',
    ].join('\n'),
    'mark-synced': [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      ': "${CLOUD_WORKSPACE_DIR:?}"',
      'cd "${CLOUD_WORKSPACE_DIR}"',
      'if ! git diff --cached --quiet --binary HEAD; then',
      '  git -c user.name=\'Cloud Agent\' -c user.email=\'cloud-agent@example.invalid\' commit -q -m \'cloud-agent synced changes\'',
      'fi',
    ].join('\n'),
  };

  for (const [name, content] of Object.entries(scripts)) {
    const scriptPath = path.join(scriptsDir, name);
    fs.writeFileSync(scriptPath, `${content}\n`, { encoding: 'utf8', mode: 0o755 });
  }

  const projectConfigFixturePath = path.join(
    repoRoot,
    'packages',
    'frontend-sdk',
    'src',
    'integration',
    '__tests__',
    'fixtures',
    'cloud-orchestrator',
    'common',
    'cloud-agent-project-config.json',
  );
  fs.writeFileSync(
    path.join(scriptsDir, 'cloud-agent.json'),
    `${fs.readFileSync(projectConfigFixturePath, 'utf8').trim()}\n`,
    { encoding: 'utf8' },
  );
}

function initializeGitWorkspace(workspaceDir: string): void {
  execFileSync('git', ['init'], { cwd: workspaceDir, stdio: 'ignore' });
  execFileSync('git', ['config', 'user.email', 'cloud-e2e@example.invalid'], { cwd: workspaceDir });
  execFileSync('git', ['config', 'user.name', 'Cloud E2E'], { cwd: workspaceDir });
}

function findRepoRoot(fromDir: string): string {
  let current = fromDir;
  for (let i = 0; i < 10; i += 1) {
    const candidate = path.join(current, 'application', 'python', 'agent_terminal_app', 'default_config', 'config.json');
    if (fs.existsSync(candidate)) {
      return current;
    }
    const next = path.dirname(current);
    if (next === current) {
      break;
    }
    current = next;
  }
  throw new Error(`Unable to find repo root from ${fromDir}`);
}

function copyDefaultConfigRoot(targetRoot: string): string {
  const repoRoot = findRepoRoot(process.cwd());
  const source = path.join(repoRoot, 'application', 'python', 'agent_terminal_app', 'default_config');
  fs.cpSync(source, targetRoot, {
    recursive: true,
    filter: (src) => !src.split(path.sep).includes('.plugin_cache'),
  });
  return path.join(targetRoot, 'config.json');
}

function patchDefaultCloudConfig(options: {
  configPath: string;
  orchestratorUrl: string;
  workspaceDir: string;
}): void {
  const cfg = JSON.parse(fs.readFileSync(options.configPath, 'utf8'));
  cfg.application.cloud_agent.orchestrator_url = options.orchestratorUrl;
  cfg.application.cloud_agent.orchestrator_token =
    process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN || '';
  cfg.application.cloud_agent.workspace_dir = options.workspaceDir;
  cfg.application.cloud_agent.config_assets.max_top_level_entry_bytes = 1_000_000;
  fs.writeFileSync(options.configPath, JSON.stringify(cfg, null, 2), 'utf8');
}

type ListedMessages = Awaited<ReturnType<RestAgentBackend['listMessages']>>;

function toolNamesFromMessages(messages: ListedMessages): string[] {
  return messages.messages
    .map((entry) => entry.message)
    .filter((message) => message.role === 'tool')
    .map((message) => (message.metadata || {}).tool_name)
    .filter((name): name is string => typeof name === 'string' && name.length > 0);
}

function expectShellAndApplyPatch(messages: ListedMessages, label: string): void {
  const toolNames = toolNamesFromMessages(messages);
  const serialized = JSON.stringify(messages.messages);
  expect(
    toolNames.some((name) => name === 'shell' || name === 'shell_command'),
    `${label}: expected shell or shell_command tool call, saw ${toolNames.join(', ')}`,
  ).toBe(true);
  expect(
    toolNames.includes('apply_patch') || serialized.includes('apply_patch'),
    `${label}: expected apply_patch tool call or intercepted apply_patch command, saw ${toolNames.join(', ')}`,
  ).toBe(true);
}

function compiledSystemText(messages: ListedMessages): string {
  for (const entry of messages.messages) {
    const message = entry.message;
    if (message.role !== 'system') continue;
    const compiled = message.metadata?.compiled_content;
    if (typeof compiled === 'string' && compiled.length > 0) {
      return compiled;
    }
    if (typeof message.content === 'string' && message.content.length > 0) {
      return message.content;
    }
  }
  return '';
}

function expectDefaultCodexDeveloperMessage(messages: ListedMessages, label: string): void {
  const compiled = compiledSystemText(messages);
  expect(compiled, `${label}: expected compiled default Codex developer message`).toContain(
    'You are a coding agent running in the Codex CLI',
  );
  expect(compiled, `${label}: expected Codex template substitution`).not.toContain(
    '{{CODEX_DEVELOPER_MESSAGE}}',
  );
}

function hasToolResult(
  messages: ListedMessages,
  toolName: string,
  contentIncludes: string,
): boolean {
  return messages.messages.some((entry) => {
    const message = entry.message;
    return (
      message.role === 'tool' &&
      message.metadata?.tool_name === toolName &&
      message.content.includes(contentIncludes)
    );
  });
}

function hasPendingToolCall(messages: ListedMessages): boolean {
  const answered = new Set<string>();
  for (const entry of messages.messages) {
    const message = entry.message;
    const toolCallId = message.metadata?.tool_call_id;
    if (message.role === 'tool' && typeof toolCallId === 'string' && toolCallId.length > 0) {
      answered.add(toolCallId);
    }
  }

  for (const entry of [...messages.messages].reverse()) {
    const message = entry.message;
    if (message.role !== 'assistant') {
      continue;
    }
    const calls = message.metadata?.tool_calls;
    if (!Array.isArray(calls) || calls.length === 0) {
      return false;
    }
    return calls.some((call) => {
      const callId = typeof call?.id === 'string' ? call.id : undefined;
      return callId ? !answered.has(callId) : true;
    });
  }

  return false;
}

function summarizeMessages(messages: ListedMessages): string {
  return messages.messages
    .slice(-8)
    .map((entry) => {
      const message = entry.message;
      const metadata = message.metadata || {};
      const toolName = typeof metadata.tool_name === 'string' ? ` tool=${metadata.tool_name}` : '';
      const calls = Array.isArray(metadata.tool_calls)
        ? ` tool_calls=${metadata.tool_calls
            .map((call) => call?.function?.name || call?.name || call?.id || '?')
            .join(',')}`
        : '';
      const content = String(message.content || '').replace(/\s+/g, ' ').slice(0, 120);
      return `${entry.index}:${message.role}${toolName}${calls} ${content}`;
    })
    .join(' | ');
}

function hasAssistantOrToolAfter(messages: ListedMessages, startCount: number): boolean {
  return messages.messages
    .slice(startCount)
    .some((entry) => entry.message.role === 'assistant' || entry.message.role === 'tool');
}

async function waitForRequestIdle(options: {
  backend: RestAgentBackend;
  sessionId: string;
  requestId?: string;
  startCount: number;
  label: string;
  timeoutMs: number;
  intervalMs?: number;
  debugContent?: () => string | Promise<string>;
}): Promise<ListedMessages> {
  const intervalMs = options.intervalMs ?? 1000;
  const deadline = Date.now() + options.timeoutMs;
  let observedRequest = !options.requestId;
  let latest: ListedMessages | null = null;

  while (Date.now() < deadline) {
    latest = await options.backend.listMessages(options.sessionId);
    if (
      options.requestId &&
      (latest.activeRequestId === options.requestId ||
        hasAssistantOrToolAfter(latest, options.startCount))
    ) {
      observedRequest = true;
    }
    if (
      observedRequest &&
      latest.activeRequestId === null &&
      hasAssistantOrToolAfter(latest, options.startCount)
    ) {
      return latest;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  const messages = latest ?? await options.backend.listMessages(options.sessionId);
  const debug = options.debugContent ? await options.debugContent() : '';
  throw new Error(
    [
      `${options.label}: request did not become idle before timeout`,
      `request_id=${options.requestId || '<unknown>'}`,
      `active_request_id=${messages.activeRequestId || '<none>'}`,
      `message_count=${messages.messages.length}`,
      `recent_messages=${summarizeMessages(messages)}`,
      debug ? `debug=${debug}` : '',
    ]
      .filter(Boolean)
      .join('\n'),
  );
}

function expectCompletedVisibleTurn(messages: ListedMessages, startCount: number, label: string): void {
  expect(messages.activeRequestId, `${label}: request should be idle`).toBeNull();
  expect(hasAssistantOrToolAfter(messages, startCount), `${label}: expected assistant/tool activity`).toBe(true);
  expect(hasPendingToolCall(messages), `${label}: expected no pending tool call`).toBe(false);
}

function writeFileToolCall(filePath: string, content: string): Record<string, any> {
  return {
    id: `call_write_${filePath.replace(/[^A-Za-z0-9_]/g, '_')}`,
    type: 'function',
    function: {
      name: 'write_file',
      arguments: JSON.stringify({ file_path: filePath, content }),
    },
  };
}

async function readCloudText(
  cloudTransport: CloudTransport,
  filePath: string,
): Promise<string | null> {
  const result = await cloudTransport.request<{ content?: string }>({
    method: 'GET',
    path: `/cloud-agent/workspace/files/${filePath}`,
    timeoutMs: 30_000,
  });
  return result.status === 200 && typeof result.data.content === 'string'
    ? result.data.content
    : null;
}

async function waitForCloudInstanceRunning(
  cloudLink: ReturnType<typeof parseCloudConnectionLink>,
  timeoutMs = 240_000,
): Promise<void> {
  const instanceId = cloudLink.instanceId;
  if (!instanceId) {
    throw new Error(`cloud link is missing an instance hint: ${JSON.stringify(cloudLink)}`);
  }
  await waitForAsync(
    async () => {
      const response = await fetch(`${cloudLink.orchestratorUrl}/instances/${instanceId}`);
      const instance = await response.json();
      if (instance.state === 'failed') {
        throw new Error(`cloud runtime failed: ${JSON.stringify(instance)}`);
      }
      return instance.state === 'running';
    },
    { timeoutMs, intervalMs: 1000 },
  );
}

function cloudTransportFromLink(
  cloudLink: ReturnType<typeof parseCloudConnectionLink>,
  defaultRequestTimeoutMs: number,
): CloudTransport {
  return new CloudTransport({
    orchestratorUrl: cloudLink.orchestratorUrl,
    connectionId: cloudLink.connectionId,
    instanceId: cloudLink.instanceId,
    token: cloudLink.token,
    defaultRequestTimeoutMs,
  });
}

function requireCloudInstanceId(cloudLink: ReturnType<typeof parseCloudConnectionLink>): string {
  if (!cloudLink.instanceId) {
    throw new Error(`cloud link is missing an instance hint: ${JSON.stringify(cloudLink)}`);
  }
  return cloudLink.instanceId;
}

async function startCloudSessionAgentAndWaitForLink(
  localBackend: RestAgentBackend,
  sessionId: string,
  timeoutMs = 420_000,
): Promise<ReturnType<typeof parseCloudConnectionLink>> {
  const startResult = await localBackend.executeAction({
    pluginId: 'cloud',
    actionId: 'cloud.start_session_agent',
    actionOwner: 'application',
    inputs: { session_id: sessionId },
  });
  expect(startResult.status, JSON.stringify(startResult, null, 2)).toBe('ok');

  let rawLink =
    typeof (startResult.result as any).connection_link === 'string'
      ? ((startResult.result as any).connection_link as string)
      : '';

  if (!rawLink) {
    await waitForAsync(
      async () => {
        const checkResult = await localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.check_session_agent',
          actionOwner: 'application',
          inputs: { session_id: sessionId },
        });
        if (checkResult.status !== 'ok') {
          throw new Error(`cloud.check_session_agent failed: ${JSON.stringify(checkResult, null, 2)}`);
        }
        const result = checkResult.result as any;
        if (result.state === 'failed') {
          throw new Error(`cloud startup failed: ${JSON.stringify(result, null, 2)}`);
        }
        if (typeof result.connection_link === 'string' && result.connection_link) {
          rawLink = result.connection_link;
          return true;
        }
        return false;
      },
      { timeoutMs, intervalMs: 2_000 },
    );
  }

  return parseCloudConnectionLink(rawLink);
}

function expectRuntimeImagePreinstalledPlugins(): void {
  if (!IS_LOCAL_CLOUD_ORCHESTRATOR_E2E) {
    return;
  }

  const script = `
import importlib.util
import json
from pathlib import Path

root = Path("/opt/ai-agent-platform/cloud-runtime-plugin-bundle")
manifest = json.loads((root / "manifest.json").read_text())
preinstalled = set(manifest.get("preinstalled_plugins", []))
expected = ["cloud-agent-app", "codex-tools", "session-title-app"]

missing = [name for name in expected if name not in preinstalled]
if missing:
    raise AssertionError(f"missing preinstalled plugins: {missing}; manifest={manifest}")

for name in expected:
    descriptor_path = root / "bundled_plugins" / name / "agent_plugin.json"
    descriptor = json.loads(descriptor_path.read_text())
    if descriptor.get("preinstalled") is not True:
        raise AssertionError(f"{name} descriptor is not marked preinstalled: {descriptor}")

for module in ["cloud_agent_app", "codex_tools", "session_title_app"]:
    if importlib.util.find_spec(module) is None:
        raise AssertionError(f"module is not importable: {module}")
`;

  execFileSync(
    'docker',
    ['run', '--rm', 'cloud-agent-runtime:latest', 'python3', '-c', script],
    { stdio: 'pipe' },
  );
}

function expectCloudRuntimePluginCacheEmpty(orchestrator: StartedCloudOrchestrator): void {
  if (!IS_LOCAL_CLOUD_ORCHESTRATOR_E2E) {
    return;
  }

  const pluginCache = path.join(
    orchestrator.dataDir,
    'runtime-cache',
    'plugin_cache',
    'plugins',
  );
  if (!fs.existsSync(pluginCache)) {
    return;
  }

  const entries = fs
    .readdirSync(pluginCache, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();

  expect(entries).toEqual([]);
}

async function runDefaultConfigCodexChain(options: {
  orchestrator: StartedCloudOrchestrator;
  agentId: 'codex-openrouter' | 'codex-openai';
}): Promise<void> {
  const workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), `cl-cloud-${options.agentId}-workspace-`));
  initializeGitWorkspace(workspaceDir);
  writeCloudAgentScripts(workspaceDir);
  fs.writeFileSync(path.join(workspaceDir, 'seed.txt'), 'alpha\n', 'utf8');
  execFileSync('git', ['add', 'seed.txt'], { cwd: workspaceDir });
  execFileSync('git', ['commit', '-m', 'initial seed'], { cwd: workspaceDir, stdio: 'ignore' });

  const configRoot = fs.mkdtempSync(path.join(os.tmpdir(), `cl-cloud-${options.agentId}-default-config-`));
  const configPath = copyDefaultConfigRoot(configRoot);
  patchDefaultCloudConfig({
    configPath,
    orchestratorUrl: options.orchestrator.baseUrl,
    workspaceDir,
  });

  const localServer = await startBackendServer({
    config: {},
    configPath,
    cwd: workspaceDir,
    startupTimeoutMs: 240_000,
    env: {
      CONFIG_DIR: configRoot,
      WORKING_DIR: workspaceDir,
      // Do not pass provider API keys here. Empty values would override the
      // backend application's normal dotenv lookup from the current directory.
    },
  });

  try {
    const localBackend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
    });
    const created = await localBackend.createSession({ agentId: options.agentId });
    const sessionId = created.session.session_id;

    const codexTurnOverrides = {
      max_output_chars: 20_000,
      system_message_as_instructions: false,
      strip_leading_system_or_developer_message: false,
    };

    const localFirstStartCount = (await localBackend.listMessages(sessionId)).messages.length;
    const localFirstSend = await localBackend.sendMessage(sessionId, {
      message: {
        role: 'user',
        content: [
          'Use tools only for the file work.',
          'First use the shell_command tool or shell tool to run a bash command that reads seed.txt.',
          'Use shell only for reading; do not write files with shell.',
          'Then use the apply_patch tool with exactly this patch:',
          '*** Begin Patch',
          '*** Add File: chain.txt',
          '+local1=alpha',
          '*** End Patch',
          'After applying the patch, use shell_command or shell to read chain.txt again.',
          'Do not reply until chain.txt contains exactly local1=alpha.',
          'Reply done after the patch is applied.',
        ].join('\n'),
      },
      configOverrides: codexTurnOverrides,
    });
    const localFirstMessages = await waitForRequestIdle({
      backend: localBackend,
      sessionId,
      requestId: localFirstSend.request_id,
      startCount: localFirstStartCount,
      label: `${options.agentId} local first turn`,
      timeoutMs: 180_000,
      debugContent: () =>
        fs.existsSync(path.join(workspaceDir, 'chain.txt'))
          ? fs.readFileSync(path.join(workspaceDir, 'chain.txt'), 'utf8')
          : '<missing chain.txt>',
    });
    expectCompletedVisibleTurn(
      localFirstMessages,
      localFirstStartCount,
      `${options.agentId} local first turn`,
    );
    expect(fs.readFileSync(path.join(workspaceDir, 'chain.txt'), 'utf8').trim()).toBe('local1=alpha');
    expectShellAndApplyPatch(
      localFirstMessages,
      `${options.agentId} local first turn`,
    );
    expectDefaultCodexDeveloperMessage(
      localFirstMessages,
      `${options.agentId} local first turn`,
    );

    const cloudLink = await startCloudSessionAgentAndWaitForLink(localBackend, sessionId);
    expect(cloudLink.connectionId).toBeTruthy();
    await waitForCloudInstanceRunning(cloudLink, 300_000);
    const cloudTransport = cloudTransportFromLink(cloudLink, 180_000);
    const cloudBackend = new RestAgentBackend({ transport: cloudTransport });

    const cloudStartCount = (await cloudBackend.listMessages(sessionId)).messages.length;
    const cloudSend = await cloudBackend.sendMessage(sessionId, {
      message: {
        role: 'user',
        content: [
          'Use tools only for the file work.',
          'First use the shell_command tool or shell tool to run a bash command that reads chain.txt.',
          'Use shell only for reading; do not write files with shell.',
          'Then use the apply_patch tool with exactly this patch:',
          '*** Begin Patch',
          '*** Update File: chain.txt',
          '@@',
          ' local1=alpha',
          '+cloud2=alpha-bravo',
          '*** End Patch',
          'After applying the patch, use shell_command or shell to read chain.txt again.',
          'Do not reply until chain.txt contains exactly two lines: local1=alpha, then cloud2=alpha-bravo.',
          'Reply done after the patch is applied.',
        ].join('\n'),
      },
      configOverrides: codexTurnOverrides,
    });
    const cloudMessagesAfterTurn = await waitForRequestIdle({
      backend: cloudBackend,
      sessionId,
      requestId: cloudSend.request_id,
      startCount: cloudStartCount,
      label: `${options.agentId} cloud turn`,
      timeoutMs: 180_000,
      debugContent: async () => (await readCloudText(cloudTransport, 'chain.txt')) || '<missing chain.txt>',
    });
    expectCompletedVisibleTurn(
      cloudMessagesAfterTurn,
      cloudStartCount,
      `${options.agentId} cloud turn`,
    );
    expect((await readCloudText(cloudTransport, 'chain.txt'))?.trim()).toBe(
      'local1=alpha\ncloud2=alpha-bravo',
    );
    expectShellAndApplyPatch(
      cloudMessagesAfterTurn,
      `${options.agentId} cloud turn`,
    );
    expectDefaultCodexDeveloperMessage(
      cloudMessagesAfterTurn,
      `${options.agentId} cloud turn`,
    );

    const syncDownResult = await localBackend.executeAction({
      pluginId: 'cloud',
      actionId: 'cloud.sync_down',
      actionOwner: 'application',
      inputs: {
        instance_id: requireCloudInstanceId(cloudLink),
        session_id: sessionId,
        workspace_dir: workspaceDir,
      },
    });
    expect(syncDownResult.status, JSON.stringify(syncDownResult, null, 2)).toBe('ok');
    expect(fs.readFileSync(path.join(workspaceDir, 'chain.txt'), 'utf8').trim()).toBe(
      'local1=alpha\ncloud2=alpha-bravo',
    );

    const closeResult = await localBackend.executeAction({
      pluginId: 'cloud',
      actionId: 'cloud.close_session',
      actionOwner: 'application',
      inputs: {
        instance_id: requireCloudInstanceId(cloudLink),
        session_id: sessionId,
        workspace_dir: workspaceDir,
      },
    });
    expect(closeResult.status, JSON.stringify(closeResult, null, 2)).toBe('ok');

    const localFinalStartCount = (await localBackend.listMessages(sessionId)).messages.length;
    const localFinalSend = await localBackend.sendMessage(sessionId, {
      message: {
        role: 'user',
        content: [
          'Use tools only for the file work.',
          'First use the shell_command tool or shell tool to run a bash command that reads chain.txt.',
          'Use shell only for reading; do not write files with shell.',
          'Then use the apply_patch tool with exactly this patch:',
          '*** Begin Patch',
          '*** Update File: chain.txt',
          '@@',
          ' local1=alpha',
          ' cloud2=alpha-bravo',
          '+local3=alpha-bravo-charlie',
          '*** End Patch',
          'After applying the patch, use shell_command or shell to read chain.txt again.',
          'Do not reply until chain.txt contains exactly three lines: local1=alpha, cloud2=alpha-bravo, local3=alpha-bravo-charlie.',
          'Reply done after the patch is applied.',
        ].join('\n'),
      },
      configOverrides: codexTurnOverrides,
    });
    const localFinalMessages = await waitForRequestIdle({
      backend: localBackend,
      sessionId,
      requestId: localFinalSend.request_id,
      startCount: localFinalStartCount,
      label: `${options.agentId} final local turn`,
      timeoutMs: 180_000,
      debugContent: () =>
        fs.existsSync(path.join(workspaceDir, 'chain.txt'))
          ? fs.readFileSync(path.join(workspaceDir, 'chain.txt'), 'utf8')
          : '<missing chain.txt>',
    });
    expectCompletedVisibleTurn(
      localFinalMessages,
      localFinalStartCount,
      `${options.agentId} final local turn`,
    );
    expect(fs.readFileSync(path.join(workspaceDir, 'chain.txt'), 'utf8').trim()).toBe(
      'local1=alpha\ncloud2=alpha-bravo\nlocal3=alpha-bravo-charlie',
    );
    expectShellAndApplyPatch(
      localFinalMessages,
      `${options.agentId} final local turn`,
    );
    expectDefaultCodexDeveloperMessage(
      localFinalMessages,
      `${options.agentId} final local turn`,
    );
  } finally {
    await localServer.stop();
    fs.rmSync(workspaceDir, { recursive: true, force: true });
    fs.rmSync(configRoot, { recursive: true, force: true });
  }
}

describe('cloud orchestrator e2e (frontend SDK -> local app action -> orchestrator -> cloud runtime)', () => {
  let stopAll: Array<() => Promise<void>> = [];

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'opens a cloud session through CloudTransport and syncs workspace files back down',
    async () => {
      const orchestrator = await startCloudOrchestratorForE2E();
      stopAll.push(orchestrator.stop);
      expectRuntimeImagePreinstalledPlugins();

      const workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-workspace-'));
      initializeGitWorkspace(workspaceDir);
      writeCloudAgentScripts(workspaceDir);
      fs.writeFileSync(path.join(workspaceDir, '.gitignore'), 'ignored-local.txt\n', 'utf8');
      fs.writeFileSync(path.join(workspaceDir, 'local.txt'), 'local file before edit\n', 'utf8');
      execFileSync('git', ['add', '.gitignore', 'local.txt'], { cwd: workspaceDir });
      execFileSync('git', ['commit', '-m', 'initial workspace'], { cwd: workspaceDir, stdio: 'ignore' });
      fs.writeFileSync(path.join(workspaceDir, 'local.txt'), 'local file\n', 'utf8');
      fs.writeFileSync(path.join(workspaceDir, 'staged-new.txt'), 'staged file\n', 'utf8');
      execFileSync('git', ['add', 'staged-new.txt'], { cwd: workspaceDir });
      fs.writeFileSync(path.join(workspaceDir, 'unstaged-new.txt'), 'unstaged file\n', 'utf8');
      fs.writeFileSync(path.join(workspaceDir, 'ignored-local.txt'), 'should not transfer\n', 'utf8');
      const configRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-config-'));
      fs.mkdirSync(path.join(configRoot, 'system_messages'), { recursive: true });
      fs.writeFileSync(
        path.join(configRoot, 'system_messages', 'test.md'),
        'cloud config asset intact\n',
        'utf8',
      );
      fs.writeFileSync(path.join(configRoot, '.env'), 'SHOULD_NOT_COPY=1\n', 'utf8');
      const largeDir = path.join(configRoot, 'large_dir');
      fs.mkdirSync(largeDir, { recursive: true });
      fs.writeFileSync(path.join(largeDir, 'payload.bin'), 'x'.repeat(128), 'utf8');
      const configPath = path.join(configRoot, 'config.json');
      fs.writeFileSync(
        configPath,
        JSON.stringify(
          localBackendConfig({
            orchestratorUrl: orchestrator.baseUrl,
            workspaceDir,
          }),
          null,
          2,
        ),
        'utf8',
      );

      const localServer = await startBackendServer({
        config: {},
        configPath,
        startupTimeoutMs: 240_000,
        env: {
          CONFIG_DIR: configRoot,
          WORKING_DIR: workspaceDir,
        },
      });
      stopAll.push(async () => {
        fs.rmSync(workspaceDir, { recursive: true, force: true });
        fs.rmSync(configRoot, { recursive: true, force: true });
        await localServer.stop();
      });

      const localBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
      });

      const created = await localBackend.createSession({ agentId: 'default' });
      const sessionId = created.session.session_id;
      await localBackend.appendMessage(sessionId, {
        role: 'user',
        content: 'local hello',
      });

      const cloudLink = await startCloudSessionAgentAndWaitForLink(localBackend, sessionId);
      expect(cloudLink.sessionId).toBe(sessionId);
      expect(cloudLink.connectionId).toBeTruthy();
      await waitForCloudInstanceRunning(cloudLink);

      const cloudTransport = cloudTransportFromLink(cloudLink, 30_000);
      const cloudBackend = new RestAgentBackend({ transport: cloudTransport });

      const cloudSessions = await cloudBackend.listSessions();
      expect(cloudSessions.some((session) => session.session_id === sessionId)).toBe(true);
      await expect(cloudBackend.listAgents()).resolves.toContain('default');
      expectCloudRuntimePluginCacheEmpty(orchestrator);

      const cloudMessages = await cloudBackend.listMessages(sessionId);
      expect(cloudMessages.messages[0]?.message.content).toBe('local hello');

      await cloudBackend.send(sessionId);
      await waitForAsync(async () => {
        const messages = await cloudBackend.listMessages(sessionId);
        return messages.messages.length >= 2;
      }, { timeoutMs: 30_000, intervalMs: 500 });

      const transferredLocalFile = await cloudTransport.request<{ content: string }>({
        method: 'GET',
        path: '/cloud-agent/workspace/files/local.txt',
        timeoutMs: 30_000,
      });
      expect(transferredLocalFile.data.content).toBe('local file\n');
      const ignoredProbe = await cloudTransport.request({
        method: 'GET',
        path: '/cloud-agent/workspace/files/ignored-local.txt',
        timeoutMs: 30_000,
      });
      expect(ignoredProbe.status).toBe(404);
      await expect(
        cloudTransport.request<{ content: string }>({
          method: 'GET',
          path: '/cloud-agent/workspace/files/staged-new.txt',
          timeoutMs: 30_000,
        }),
      ).resolves.toMatchObject({ data: { content: 'staged file\n' } });
      await expect(
        cloudTransport.request<{ content: string }>({
          method: 'GET',
          path: '/cloud-agent/workspace/files/unstaged-new.txt',
          timeoutMs: 30_000,
        }),
      ).resolves.toMatchObject({ data: { content: 'unstaged file\n' } });

      const transferredConfigAsset = await cloudTransport.request<{ content: string }>({
        method: 'GET',
        path: '/cloud-agent/config-assets/files/system_messages/test.md',
        timeoutMs: 30_000,
      });
      expect(transferredConfigAsset.data.content).toBe('cloud config asset intact\n');

      const cloudCreatedSession = await cloudBackend.createSession({ agentId: 'default' });
      const cloudCreatedSessionId = cloudCreatedSession.session.session_id;
      const cloudSessionsAfterCreate = await cloudBackend.listSessions();
      expect(
        cloudSessionsAfterCreate.some((session) => session.session_id === cloudCreatedSessionId),
      ).toBe(true);
      await cloudBackend.appendMessage(cloudCreatedSessionId, {
        role: 'assistant',
        content: 'Calling write_file.',
        metadata: {
          tool_calls: [writeFileToolCall('from-cloud.txt', 'synced from cloud\n')],
        },
      });
      await cloudBackend.send(cloudCreatedSessionId);
      await waitForAsync(
        async () =>
          hasToolResult(
            await cloudBackend.listMessages(cloudCreatedSessionId),
            'write_file',
            'from-cloud.txt',
          ),
        { timeoutMs: 30_000, intervalMs: 500 },
      );

      const syncDownResult = await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.sync_down',
        actionOwner: 'application',
        inputs: {
          instance_id: requireCloudInstanceId(cloudLink),
          workspace_dir: workspaceDir,
        },
      });
      expect(syncDownResult.status, JSON.stringify(syncDownResult, null, 2)).toBe('ok');

      expect(fs.readFileSync(path.join(workspaceDir, 'from-cloud.txt'), 'utf8')).toBe(
        'synced from cloud\n',
      );

      await cloudBackend.appendMessage(cloudCreatedSessionId, {
        role: 'assistant',
        content: 'Calling write_file again.',
        metadata: {
          tool_calls: [writeFileToolCall('from-cloud-2.txt', 'second sync from cloud\n')],
        },
      });
      await cloudBackend.send(cloudCreatedSessionId);
      await waitForAsync(
        async () =>
          hasToolResult(
            await cloudBackend.listMessages(cloudCreatedSessionId),
            'write_file',
            'from-cloud-2.txt',
          ),
        { timeoutMs: 30_000, intervalMs: 500 },
      );

      const secondSyncDownResult = await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.sync_down',
        actionOwner: 'application',
        inputs: {
          instance_id: requireCloudInstanceId(cloudLink),
          workspace_dir: workspaceDir,
        },
      });
      expect(
        secondSyncDownResult.status,
        JSON.stringify(secondSyncDownResult, null, 2),
      ).toBe('ok');
      expect(fs.readFileSync(path.join(workspaceDir, 'from-cloud-2.txt'), 'utf8')).toBe(
        'second sync from cloud\n',
      );

      const closeResult = await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.close_session',
        actionOwner: 'application',
        inputs: {
          instance_id: requireCloudInstanceId(cloudLink),
          session_id: sessionId,
          workspace_dir: workspaceDir,
        },
      });
      expect(closeResult.status, JSON.stringify(closeResult, null, 2)).toBe('ok');
      const localMessages = await localBackend.listMessages(sessionId);
      expect(localMessages.messages.length).toBeGreaterThanOrEqual(2);
    },
    TEST_TIMEOUT_MS,
  );

  it(
    'routes two cloud sessions through one connection-scoped CloudTransport',
    async () => {
      const orchestrator = await startCloudOrchestratorForE2E();
      stopAll.push(orchestrator.stop);

      const workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-shared-workspace-'));
      initializeGitWorkspace(workspaceDir);
      writeCloudAgentScripts(workspaceDir);
      fs.writeFileSync(path.join(workspaceDir, 'shared.txt'), 'shared workspace\n', 'utf8');
      execFileSync('git', ['add', 'shared.txt'], { cwd: workspaceDir });
      execFileSync('git', ['commit', '-m', 'initial workspace'], { cwd: workspaceDir, stdio: 'ignore' });

      const configRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-shared-config-'));
      const configPath = path.join(configRoot, 'config.json');
      fs.writeFileSync(
        configPath,
        JSON.stringify(
          localBackendConfig({
            orchestratorUrl: orchestrator.baseUrl,
            workspaceDir,
          }),
          null,
          2,
        ),
        'utf8',
      );

      const localServer = await startBackendServer({
        config: {},
        configPath,
        startupTimeoutMs: 240_000,
        env: {
          CONFIG_DIR: configRoot,
          WORKING_DIR: workspaceDir,
        },
      });
      stopAll.push(async () => {
        fs.rmSync(workspaceDir, { recursive: true, force: true });
        fs.rmSync(configRoot, { recursive: true, force: true });
        await localServer.stop();
      });

      const localBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
      });

      const session1 = (await localBackend.createSession({ agentId: 'default' })).session.session_id;
      const session2 = (await localBackend.createSession({ agentId: 'default' })).session.session_id;
      await localBackend.appendMessage(session1, { role: 'user', content: 'local hello one' });
      await localBackend.appendMessage(session2, { role: 'user', content: 'local hello two' });

      const link1 = await startCloudSessionAgentAndWaitForLink(localBackend, session1);
      expect(link1.connectionId).toBeTruthy();
      await waitForCloudInstanceRunning(link1);

      const link2 = await startCloudSessionAgentAndWaitForLink(localBackend, session2);
      expect(link2.connectionId).toBe(link1.connectionId);
      expect(requireCloudInstanceId(link2)).not.toBe(requireCloudInstanceId(link1));
      await waitForCloudInstanceRunning(link2);

      const cloudTransport = cloudTransportFromLink(link1, 30_000);
      const cloudBackend = new RestAgentBackend({ transport: cloudTransport });
      const cloudSessions = await cloudBackend.listSessions();
      expect(cloudSessions.some((session) => session.session_id === session1)).toBe(true);
      expect(cloudSessions.some((session) => session.session_id === session2)).toBe(true);

      const messages1 = await cloudBackend.listMessages(session1);
      const messages2 = await cloudBackend.listMessages(session2);
      expect(messages1.messages[0]?.message.content).toBe('local hello one');
      expect(messages2.messages[0]?.message.content).toBe('local hello two');

      const titleResult = await cloudBackend.executeSessionAction!({
        sessionId: session2,
        pluginId: 'session_title',
        actionId: 'set_session_title',
        actionOwner: 'application',
        inputs: {
          session_id: session2,
          title: 'Cloud title two',
        },
      });
      expect(titleResult.status).toBe('ok');

      await waitForAsync(async () => {
        const sessions = await cloudBackend.listSessions();
        const first = sessions.find((session) => session.session_id === session1);
        const second = sessions.find((session) => session.session_id === session2);
        return (
          (second?.metadata?.title as string | undefined) === 'Cloud title two' &&
          !first?.metadata?.title
        );
      }, { timeoutMs: 30_000, intervalMs: 500 });

      await cloudBackend.send(session1);
      await cloudBackend.send(session2);
      await waitForAsync(async () => {
        const [next1, next2] = await Promise.all([
          cloudBackend.listMessages(session1),
          cloudBackend.listMessages(session2),
        ]);
        return next1.messages.length >= 2 && next2.messages.length >= 2;
      }, { timeoutMs: 60_000, intervalMs: 500 });

      const connectionResp = await fetch(`${orchestrator.baseUrl}/connections/${link1.connectionId}`);
      const connection = await connectionResp.json();
      expect(connection.instance_ids).toEqual(
        expect.arrayContaining([requireCloudInstanceId(link1), requireCloudInstanceId(link2)]),
      );
    },
    TEST_TIMEOUT_MS,
  );
});

describeCodexDefaultConfigIf('cloud orchestrator default-config Codex provider e2e', () => {
  let orchestrator: StartedCloudOrchestrator;

  beforeAll(async () => {
    orchestrator = await startCloudOrchestratorForE2E();
  }, CODEX_DEFAULT_CONFIG_HOOK_TIMEOUT_MS);

  afterAll(async () => {
    if (orchestrator) {
      await orchestrator.stop();
    }
  }, CODEX_DEFAULT_CONFIG_HOOK_TIMEOUT_MS);

  for (const agentId of ['codex-openrouter', 'codex-openai'] as const) {
    it(
      `runs local-cloud-local bash and apply_patch chain with ${agentId}`,
      async () => {
        await runDefaultConfigCodexChain({ orchestrator, agentId });
      },
      TEST_TIMEOUT_MS,
    );
  }
});

describeCodexDefaultConfigEc2If('cloud orchestrator EC2 default-config Codex provider e2e', () => {
  let orchestrator: StartedCloudOrchestrator;

  beforeAll(async () => {
    orchestrator = await startCloudOrchestratorForE2E();
  }, CODEX_DEFAULT_CONFIG_HOOK_TIMEOUT_MS);

  afterAll(async () => {
    if (orchestrator) {
      await orchestrator.stop();
    }
  }, CODEX_DEFAULT_CONFIG_HOOK_TIMEOUT_MS);

  for (const agentId of ['codex-openrouter', 'codex-openai'] as const) {
    it(
      `runs EC2 local-cloud-local bash and apply_patch chain with ${agentId}`,
      async () => {
        await runDefaultConfigCodexChain({ orchestrator, agentId });
      },
      TEST_TIMEOUT_MS,
    );
  }
});

describeOpenRouterIf('cloud orchestrator OpenRouter e2e', () => {
  let stopAll: Array<() => Promise<void>> = [];

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'runs local and cloud OpenRouter tool calls with config assets and sync-back',
    async () => {
      const orchestrator = await startCloudOrchestratorForE2E();
      stopAll.push(orchestrator.stop);

      const workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-openrouter-workspace-'));
      initializeGitWorkspace(workspaceDir);
      writeCloudAgentScripts(workspaceDir);
      fs.writeFileSync(path.join(workspaceDir, '.gitignore'), 'ignored-local.txt\n', 'utf8');
      execFileSync('git', ['add', '.gitignore'], { cwd: workspaceDir });
      execFileSync('git', ['commit', '-m', 'initial workspace'], { cwd: workspaceDir, stdio: 'ignore' });
      const configRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-openrouter-config-'));
      fs.mkdirSync(path.join(configRoot, 'system_messages'), { recursive: true });
      fs.writeFileSync(
        path.join(configRoot, 'system_messages', 'openrouter-e2e.md'),
        [
          'You are running a cloud orchestrator integration test.',
          'When asked to create a file, call the write_file tool.',
          'Use exactly the requested path and content.',
        ].join('\n'),
        'utf8',
      );
      fs.writeFileSync(path.join(configRoot, '.env'), 'SHOULD_NOT_COPY=1\n', 'utf8');
      const configPath = path.join(configRoot, 'config.json');
      fs.writeFileSync(
        configPath,
        JSON.stringify(
          openRouterBackendConfig({
            orchestratorUrl: orchestrator.baseUrl,
            workspaceDir,
          }),
          null,
          2,
        ),
        'utf8',
      );

      const localServer = await startBackendServer({
        config: {},
        configPath,
        startupTimeoutMs: 240_000,
        env: {
          CONFIG_DIR: configRoot,
          WORKING_DIR: workspaceDir,
          // Do not pass provider API keys here. Empty values would override the
          // backend application's normal dotenv lookup from the current directory.
        },
      });
      stopAll.push(async () => {
        fs.rmSync(workspaceDir, { recursive: true, force: true });
        fs.rmSync(configRoot, { recursive: true, force: true });
        await localServer.stop();
      });

      const localBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
      });
      const created = await localBackend.createSession({ agentId: 'default' });
      const sessionId = created.session.session_id;

      await localBackend.sendMessage(sessionId, {
        message: {
          role: 'user',
          content:
            "Use write_file to create local-openrouter.txt with exactly 'local ok\\n'. Reply done after the tool call.",
        },
      });
      await waitForAsync(
        async () => fs.existsSync(path.join(workspaceDir, 'local-openrouter.txt')),
        { timeoutMs: 120_000, intervalMs: 1000 },
      );
      expect(fs.readFileSync(path.join(workspaceDir, 'local-openrouter.txt'), 'utf8')).toBe('local ok\n');

      const cloudLink = await startCloudSessionAgentAndWaitForLink(localBackend, sessionId);
      expect(cloudLink.connectionId).toBeTruthy();
      await waitForCloudInstanceRunning(cloudLink, 300_000);
      const cloudTransport = cloudTransportFromLink(cloudLink, 120_000);
      const cloudBackend = new RestAgentBackend({ transport: cloudTransport });

      const transferredLocalFile = await cloudTransport.request<{ content: string }>({
        method: 'GET',
        path: '/cloud-agent/workspace/files/local-openrouter.txt',
        timeoutMs: 30_000,
      });
      expect(transferredLocalFile.data.content).toBe('local ok\n');

      const transferredConfigAsset = await cloudTransport.request<{ content: string }>({
        method: 'GET',
        path: '/cloud-agent/config-assets/files/system_messages/openrouter-e2e.md',
        timeoutMs: 30_000,
      });
      expect(transferredConfigAsset.data.content).toContain('cloud orchestrator integration test');

      const cloudExecutionSession = await cloudBackend.createSession({ agentId: 'default' });
      const cloudExecutionSessionId = cloudExecutionSession.session.session_id;
      const cloudSessionsAfterCreate = await cloudBackend.listSessions();
      expect(
        cloudSessionsAfterCreate.some((session) => session.session_id === cloudExecutionSessionId),
      ).toBe(true);

      await cloudBackend.sendMessage(cloudExecutionSessionId, {
        message: {
          role: 'user',
          content:
            "Use write_file to create cloud-openrouter.txt with exactly 'cloud ok\\n'. Reply done after the tool call.",
        },
      });
      await waitForAsync(
        async () =>
          hasToolResult(
            await cloudBackend.listMessages(cloudExecutionSessionId),
            'write_file',
            'cloud-openrouter.txt',
          ),
        { timeoutMs: 180_000, intervalMs: 1000 },
      );

      await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.sync_down',
        actionOwner: 'application',
        inputs: {
          instance_id: requireCloudInstanceId(cloudLink),
          workspace_dir: workspaceDir,
        },
      });

      expect(fs.readFileSync(path.join(workspaceDir, 'cloud-openrouter.txt'), 'utf8')).toBe('cloud ok\n');
    },
    TEST_TIMEOUT_MS,
  );
});