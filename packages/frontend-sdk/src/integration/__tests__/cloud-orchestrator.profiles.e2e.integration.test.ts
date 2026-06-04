import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { afterAll, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import {
  CloudTransport,
  parseCloudConnectionLink,
} from '../../transport/cloudTransport';
import {
  type StartedCloudOrchestrator,
  startBackendServer,
  startCloudOrchestratorLocal,
  waitForAsync,
} from '../harness';

const RUN = process.env.RUN_CLOUD_ORCHESTRATOR_PROFILE_E2E === '1';
const describeIf = RUN ? describe.sequential : describe.skip;
const TEST_TIMEOUT_MS = 600_000;
const HOOK_TIMEOUT_MS = 60_000;

const FIXTURES_ROOT = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  'fixtures',
  'cloud-orchestrator-profiles',
);

function findRepoRoot(fromDir: string): string {
  let current = fromDir;
  for (let i = 0; i < 10; i += 1) {
    const candidate = path.join(
      current,
      'application',
      'python',
      'agent_terminal_app',
      'default_config',
      'config.json',
    );
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

function fixturePath(...parts: string[]): string {
  return path.join(FIXTURES_ROOT, ...parts);
}

function copyDefaultConfigRoot(targetRoot: string): string {
  const repoRoot = findRepoRoot(process.cwd());
  const source = path.join(
    repoRoot,
    'application',
    'python',
    'agent_terminal_app',
    'default_config',
  );
  fs.cpSync(source, targetRoot, {
    recursive: true,
    filter: (src) => !src.split(path.sep).includes('.plugin_cache'),
  });
  return path.join(targetRoot, 'config.json');
}

function copyFixtureTree(sourceDir: string, targetDir: string): void {
  fs.cpSync(sourceDir, targetDir, { recursive: true });
}

function ensureExecutable(filePath: string): void {
  if (fs.existsSync(filePath)) {
    fs.chmodSync(filePath, 0o755);
  }
}

function sanitizeRefToken(value: string): string {
  const cleaned = value.trim().replace(/[^A-Za-z0-9._/-]+/g, '-').replace(/^[./]+|[./]+$/g, '');
  return cleaned || 'session';
}

function initializeGitWorkspace(workspaceDir: string): void {
  execFileSync('git', ['init'], { cwd: workspaceDir, stdio: 'ignore' });
  execFileSync('git', ['config', 'user.email', 'cloud-profile-e2e@example.invalid'], {
    cwd: workspaceDir,
  });
  execFileSync('git', ['config', 'user.name', 'Cloud Profile E2E'], {
    cwd: workspaceDir,
  });
}

function commitFiles(workspaceDir: string, paths: string[], message: string): void {
  execFileSync('git', ['add', ...paths], { cwd: workspaceDir });
  execFileSync('git', ['commit', '-m', message], {
    cwd: workspaceDir,
    stdio: 'ignore',
  });
}

function buildBackendConfig(configPath: string, options: {
  orchestratorUrl: string;
  workspaceDir: string;
}): void {
  const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  cfg.providers = {
    test_provider: {
      provider: 'echo_openai_like',
      model: 'test-model',
      timeout: 60,
      stream: false,
      working_directory: '${env:WORKING_DIR}',
      allowed_paths: ['${env:WORKING_DIR}'],
    },
  };
  cfg.plugins = [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:BUILTIN_PLUGINS}/codex-tools',
    'path:${env:BUILTIN_PLUGINS}/cloud-agent-app',
  ];
  cfg.agents = {
    default: {
      provider: 'test_provider',
      shell_tool_mode: 'shell_command',
    },
  };
  cfg.application.cloud_agent.orchestrator_url = options.orchestratorUrl;
  cfg.application.cloud_agent.orchestrator_token =
    process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN || '';
  cfg.application.cloud_agent.workspace_dir = options.workspaceDir;
  cfg.application.cloud_agent.config_assets.max_top_level_entry_bytes = 1_000_000;
  fs.writeFileSync(configPath, JSON.stringify(cfg, null, 2), 'utf8');
}

function writeFixtureConfigAsset(configRoot: string): void {
  const systemMessagesDir = path.join(configRoot, 'system_messages');
  fs.mkdirSync(systemMessagesDir, { recursive: true });
  fs.copyFileSync(
    fixturePath('common', 'config-assets', 'profile-e2e.md'),
    path.join(systemMessagesDir, 'profile-e2e.md'),
  );
}

function prepareWorkspaceFixture(scenario: string, workspaceDir: string): void {
  copyFixtureTree(fixturePath(scenario, 'workspace'), workspaceDir);
  ensureExecutable(path.join(workspaceDir, '.cloud-agent', 'local-stage'));
  ensureExecutable(path.join(workspaceDir, '.cloud-agent', 'install-cloud'));
  ensureExecutable(path.join(workspaceDir, '.cloud-agent', 'validate-cloud'));
}

type ProfileScenarioContext = {
  workspaceDir: string;
  configRoot: string;
  configPath: string;
  localBackend: RestAgentBackend;
  localServer: Awaited<ReturnType<typeof startBackendServer>>;
  cleanup: () => Promise<void>;
};

function validationCommandEnv(repoRoot: string, options: {
  workspaceDir: string;
  configPath: string;
}): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PYTHONPATH: [
      path.join(repoRoot, 'core', 'python'),
      path.join(repoRoot, 'application', 'python'),
      path.join(repoRoot, 'plugins', 'cloud-agent-app', 'src'),
    ].join(path.delimiter),
    BUILTIN_PLUGINS: path.join(repoRoot, 'plugins'),
    WORKING_DIR: options.workspaceDir,
    CONFIG_DIR: path.dirname(options.configPath),
  };
}

function runValidateCloudCommand(options: {
  configPath: string;
  workspaceDir: string;
}): string {
  const repoRoot = findRepoRoot(process.cwd());
  const python = process.env.PYTHON || 'python';
  return execFileSync(
    python,
    [
      '-m',
      'agent_terminal_app',
      '--config',
      options.configPath,
      'validate-cloud',
      '--workspace-dir',
      options.workspaceDir,
      '--cache-dir',
      path.join(path.dirname(options.configPath), 'cloud-validation-cache'),
    ],
    {
      cwd: repoRoot,
      env: validationCommandEnv(repoRoot, options),
      encoding: 'utf8',
    },
  );
}

function runValidateCloudCommandExpectFailure(options: {
  configPath: string;
  workspaceDir: string;
}): string {
  try {
    runValidateCloudCommand(options);
  } catch (error) {
    const output = error as { stdout?: string; stderr?: string };
    return `${output.stdout || ''}${output.stderr || ''}`;
  }
  throw new Error('validate-cloud unexpectedly succeeded');
}

async function startProfileScenario(options: {
  scenario: string;
  orchestrator: StartedCloudOrchestrator;
}): Promise<ProfileScenarioContext> {
  const workspaceDir = fs.mkdtempSync(
    path.join(os.tmpdir(), `cl-cloud-profile-${options.scenario}-workspace-`),
  );
  const configRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), `cl-cloud-profile-${options.scenario}-config-`),
  );
  prepareWorkspaceFixture(options.scenario, workspaceDir);
  const configPath = copyDefaultConfigRoot(configRoot);
  writeFixtureConfigAsset(configRoot);
  buildBackendConfig(configPath, {
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
    },
  });

  return {
    workspaceDir,
    configRoot,
    configPath,
    localServer,
    localBackend: new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
    }),
    cleanup: async () => {
      fs.rmSync(workspaceDir, { recursive: true, force: true });
      fs.rmSync(configRoot, { recursive: true, force: true });
      await localServer.stop();
    },
  };
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

function requireCloudInstanceId(
  cloudLink: ReturnType<typeof parseCloudConnectionLink>,
): string {
  if (!cloudLink.instanceId) {
    throw new Error(`cloud link is missing an instance hint: ${JSON.stringify(cloudLink)}`);
  }
  return cloudLink.instanceId;
}

async function waitForCloudInstanceRunning(
  cloudLink: ReturnType<typeof parseCloudConnectionLink>,
  timeoutMs = 240_000,
): Promise<void> {
  const instanceId = requireCloudInstanceId(cloudLink);
  await waitForAsync(
    async () => {
      const response = await fetch(
        `${cloudLink.orchestratorUrl}/instances/${instanceId}`,
      );
      const instance = await response.json();
      if (instance.state === 'failed') {
        throw new Error(`cloud runtime failed: ${JSON.stringify(instance)}`);
      }
      return instance.state === 'running';
    },
    { timeoutMs, intervalMs: 1000 },
  );
}

function shellCommandToolCall(command: string, workdir: string): Record<string, any> {
  return {
    id: `call_shell_${Math.random().toString(16).slice(2)}`,
    type: 'function',
    function: {
      name: 'shell_command',
      arguments: JSON.stringify({
        command,
        workdir,
        timeout_ms: 30_000,
        login: false,
      }),
    },
  };
}

async function waitForToolResult(options: {
  backend: RestAgentBackend;
  sessionId: string;
  toolName: string;
  contentIncludes: string;
  timeoutMs?: number;
}): Promise<void> {
  await waitForAsync(
    async () => {
      const listed = await options.backend.listMessages(options.sessionId);
      return listed.messages.some((entry) => {
        const message = entry.message;
        return (
          message.role === 'tool' &&
          message.metadata?.tool_name === options.toolName &&
          message.content.includes(options.contentIncludes)
        );
      });
    },
    { timeoutMs: options.timeoutMs ?? 60_000, intervalMs: 500 },
  );
}

async function runCloudShellCommand(options: {
  backend: RestAgentBackend;
  sessionId: string;
  workspaceDir: string;
  command: string;
  successMarker: string;
}): Promise<void> {
  await options.backend.appendMessage(options.sessionId, {
    role: 'assistant',
    content: `Running shell_command: ${options.successMarker}`,
    metadata: {
      tool_calls: [
        shellCommandToolCall(
          `${options.command} && printf '${options.successMarker}'`,
          options.workspaceDir,
        ),
      ],
    },
  });
  await options.backend.send(options.sessionId);
  await waitForToolResult({
    backend: options.backend,
    sessionId: options.sessionId,
    toolName: 'shell_command',
    contentIncludes: options.successMarker,
    timeoutMs: 120_000,
  });
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

async function startCloudSession(options: {
  backend: RestAgentBackend;
  sessionId: string;
  workspaceDir?: string;
}): Promise<{
  cloudLink: ReturnType<typeof parseCloudConnectionLink>;
  cloudTransport: CloudTransport;
  cloudBackend: RestAgentBackend;
}> {
  const startResult = await options.backend.executeAction({
    pluginId: 'cloud',
    actionId: 'cloud.start_session_agent',
    actionOwner: 'application',
    inputs: {
      session_id: options.sessionId,
      ...(options.workspaceDir ? { workspace_dir: options.workspaceDir } : {}),
    },
  });
  expect(startResult.status, JSON.stringify(startResult, null, 2)).toBe('ok');

  let rawLink =
    typeof (startResult.result as any).connection_link === 'string'
      ? ((startResult.result as any).connection_link as string)
      : '';
  if (!rawLink) {
    await waitForAsync(
      async () => {
        const checkResult = await options.backend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.check_session_agent',
          actionOwner: 'application',
          inputs: { session_id: options.sessionId },
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
      { timeoutMs: 420_000, intervalMs: 2_000 },
    );
  }

  const cloudLink = parseCloudConnectionLink(rawLink);
  await waitForCloudInstanceRunning(cloudLink, 300_000);
  const cloudTransport = cloudTransportFromLink(cloudLink, 120_000);
  return {
    cloudLink,
    cloudTransport,
    cloudBackend: new RestAgentBackend({ transport: cloudTransport }),
  };
}

describeIf(
  'cloud orchestrator standard profile e2e (local docker orchestrator)',
  () => {
    let orchestrator: StartedCloudOrchestrator | null = null;
    const cleanupFns: Array<() => Promise<void>> = [];

    afterAll(async () => {
      for (const cleanup of cleanupFns.reverse()) {
        await cleanup();
      }
      if (orchestrator) {
        await orchestrator.stop();
      }
    }, HOOK_TIMEOUT_MS);

    it(
      'runs the shipped patch default plus local stage and install hook through the real orchestrator flow',
      async () => {
        orchestrator = await startCloudOrchestratorLocal();
        const context = await startProfileScenario({
          scenario: 'working-tree-patch',
          orchestrator,
        });
        cleanupFns.push(context.cleanup);

        initializeGitWorkspace(context.workspaceDir);
        commitFiles(
          context.workspaceDir,
          [
            '.gitignore',
            'local.txt',
            '.cloud-agent/cloud-agent.json',
            '.cloud-agent/local-stage',
            '.cloud-agent/install-cloud',
          ],
          'initial workspace',
        );
        fs.writeFileSync(
          path.join(context.workspaceDir, 'local.txt'),
          'local file\n',
          'utf8',
        );
        fs.writeFileSync(
          path.join(context.workspaceDir, 'staged-new.txt'),
          'staged file\n',
          'utf8',
        );
        execFileSync('git', ['add', 'staged-new.txt'], { cwd: context.workspaceDir });
        fs.writeFileSync(
          path.join(context.workspaceDir, 'unstaged-new.txt'),
          'unstaged file\n',
          'utf8',
        );
        fs.writeFileSync(
          path.join(context.workspaceDir, 'ignored-local.txt'),
          'should not transfer\n',
          'utf8',
        );
        const validationOutput = runValidateCloudCommand({
          configPath: context.configPath,
          workspaceDir: context.workspaceDir,
        });
        expect(validationOutput).toContain('Cloud Validation Passed');

        const created = await context.localBackend.createSession({ agentId: 'default' });
        const sessionId = created.session.session_id;
        const { cloudLink, cloudTransport } = await startCloudSession({
          backend: context.localBackend,
          sessionId,
          workspaceDir: context.workspaceDir,
        });

        expect(await readCloudText(cloudTransport, 'local.txt')).toBe('local file\n');
        expect(await readCloudText(cloudTransport, 'staged-new.txt')).toBe('staged file\n');
        expect(await readCloudText(cloudTransport, 'unstaged-new.txt')).toBe(
          'unstaged file\n',
        );
        const ignoredProbe = await cloudTransport.request({
          method: 'GET',
          path: '/cloud-agent/workspace/files/ignored-local.txt',
          timeoutMs: 30_000,
        });
        expect(ignoredProbe.status).toBe(404);
        expect(await readCloudText(cloudTransport, '.env')).toContain(
          'PROFILE_E2E_SECRET=from-fixture',
        );
        expect(await readCloudText(cloudTransport, 'install.ok')).toBe('ok\n');
        const asset = await cloudTransport.request<{ content: string }>({
          method: 'GET',
          path: '/cloud-agent/config-assets/files/system_messages/profile-e2e.md',
          timeoutMs: 30_000,
        });
        expect(asset.data.content).toContain('Cloud profile integration asset');

        await cloudTransport.request({
          method: 'POST',
          path: '/cloud-agent/workspace/files',
          body: { path: 'from-cloud.txt', content: 'synced from cloud\n' },
          timeoutMs: 30_000,
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.sync_down',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        expect(
          fs.readFileSync(path.join(context.workspaceDir, 'from-cloud.txt'), 'utf8'),
        ).toBe('synced from cloud\n');

        await cloudTransport.request({
          method: 'POST',
          path: '/cloud-agent/workspace/files',
          body: { path: 'from-cloud-2.txt', content: 'second sync from cloud\n' },
          timeoutMs: 30_000,
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.sync_down',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.close_session',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        expect(
          fs.readFileSync(path.join(context.workspaceDir, 'from-cloud-2.txt'), 'utf8'),
        ).toBe('second sync from cloud\n');
      },
      TEST_TIMEOUT_MS,
    );

    it(
      'runs the clean-head branch-import profile through the real orchestrator flow',
      async () => {
        orchestrator = orchestrator || (await startCloudOrchestratorLocal());
        const context = await startProfileScenario({
          scenario: 'clean-head-branch',
          orchestrator,
        });
        cleanupFns.push(context.cleanup);

        initializeGitWorkspace(context.workspaceDir);
        commitFiles(
          context.workspaceDir,
          ['tracked.txt', '.cloud-agent/cloud-agent.json'],
          'initial workspace',
        );
        fs.writeFileSync(
          path.join(context.workspaceDir, 'tracked.txt'),
          'local dirty\n',
          'utf8',
        );
        const validationOutput = runValidateCloudCommand({
          configPath: context.configPath,
          workspaceDir: context.workspaceDir,
        });
        expect(validationOutput).toContain('Cloud Validation Passed');

        const created = await context.localBackend.createSession({ agentId: 'default' });
        const sessionId = created.session.session_id;
        const { cloudLink, cloudTransport, cloudBackend } = await startCloudSession({
          backend: context.localBackend,
          sessionId,
          workspaceDir: context.workspaceDir,
        });

        expect(await readCloudText(cloudTransport, 'tracked.txt')).toBe('base');

        const cloudExecutionSessionId = (
          await cloudBackend.createSession({ agentId: 'default' })
        ).session.session_id;
        await runCloudShellCommand({
          backend: cloudBackend,
          sessionId: cloudExecutionSessionId,
          workspaceDir: '/cloud-agent/instance/workspace',
          command: [
            'git config user.email cloud@example.invalid',
            'git config user.name "Cloud Test"',
            'printf "base\\ncloud commit\\n" > tracked.txt',
            'git add tracked.txt',
            'git commit -m "cloud commit" >/dev/null',
          ].join(' && '),
          successMarker: 'CLEAN_HEAD_COMMIT_OK',
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.sync_down',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        expect(
          fs.readFileSync(path.join(context.workspaceDir, 'tracked.txt'), 'utf8'),
        ).toBe('local dirty\n');
        const token = sanitizeRefToken(sessionId);
        const committed = execFileSync(
          'git',
          ['show', `cloud/${token}/committed:tracked.txt`],
          { cwd: context.workspaceDir, encoding: 'utf8' },
        );
        expect(committed).toBe('base\ncloud commit\n');
        const localImportRef = execFileSync(
          'git',
          ['rev-parse', `refs/cloud-agent/${token}/local-import-state`],
          { cwd: context.workspaceDir, encoding: 'utf8' },
        ).trim();
        expect(localImportRef).toMatch(/[0-9a-f]{40}/);
      },
      TEST_TIMEOUT_MS,
    );

    it(
      'runs the dirty-snapshot branch-import profile through the real orchestrator flow',
      async () => {
        orchestrator = orchestrator || (await startCloudOrchestratorLocal());
        const context = await startProfileScenario({
          scenario: 'dirty-branch',
          orchestrator,
        });
        cleanupFns.push(context.cleanup);

        initializeGitWorkspace(context.workspaceDir);
        commitFiles(
          context.workspaceDir,
          ['a.txt', 'b.txt', '.cloud-agent/cloud-agent.json'],
          'initial workspace',
        );
        fs.writeFileSync(path.join(context.workspaceDir, 'a.txt'), 'local-a\n', 'utf8');
        fs.writeFileSync(path.join(context.workspaceDir, 'b.txt'), 'local-b\n', 'utf8');
        const validationOutput = runValidateCloudCommand({
          configPath: context.configPath,
          workspaceDir: context.workspaceDir,
        });
        expect(validationOutput).toContain('Cloud Validation Passed');

        const created = await context.localBackend.createSession({ agentId: 'default' });
        const sessionId = created.session.session_id;
        const { cloudLink, cloudTransport, cloudBackend } = await startCloudSession({
          backend: context.localBackend,
          sessionId,
          workspaceDir: context.workspaceDir,
        });

        expect(await readCloudText(cloudTransport, 'a.txt')).toBe('local-a\n');
        expect(await readCloudText(cloudTransport, 'b.txt')).toBe('local-b\n');

        const cloudExecutionSessionId = (
          await cloudBackend.createSession({ agentId: 'default' })
        ).session.session_id;
        await runCloudShellCommand({
          backend: cloudBackend,
          sessionId: cloudExecutionSessionId,
          workspaceDir: '/cloud-agent/instance/workspace',
          command: [
            'git config user.email cloud@example.invalid',
            'git config user.name "Cloud Test"',
            'printf "cloud-b1\\n" > b.txt',
            'git add b.txt',
            'git commit -m "cloud b1" >/dev/null',
          ].join(' && '),
          successMarker: 'DIRTY_BRANCH_COMMIT_ONE_OK',
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.sync_down',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        expect(fs.readFileSync(path.join(context.workspaceDir, 'a.txt'), 'utf8')).toBe(
          'local-a\n',
        );
        expect(fs.readFileSync(path.join(context.workspaceDir, 'b.txt'), 'utf8')).toBe(
          'local-b\n',
        );
        const token = sanitizeRefToken(sessionId);
        expect(
          execFileSync('git', ['show', `cloud/${token}/committed:b.txt`], {
            cwd: context.workspaceDir,
            encoding: 'utf8',
          }),
        ).toBe('cloud-b1\n');
        expect(
          execFileSync('git', ['show', `refs/cloud-agent/${token}/delegated-snapshot:a.txt`], {
            cwd: context.workspaceDir,
            encoding: 'utf8',
          }),
        ).toBe('local-a\n');
        expect(
          execFileSync('git', ['show', `refs/cloud-agent/${token}/local-import-state:b.txt`], {
            cwd: context.workspaceDir,
            encoding: 'utf8',
          }),
        ).toBe('local-b\n');

        await runCloudShellCommand({
          backend: cloudBackend,
          sessionId: cloudExecutionSessionId,
          workspaceDir: '/cloud-agent/instance/workspace',
          command: [
            'printf "cloud-b2\\n" > b.txt',
            'git add b.txt',
            'git commit -m "cloud b2" >/dev/null',
            'printf "local-a\\ncloud residual\\n" > a.txt',
          ].join(' && '),
          successMarker: 'DIRTY_BRANCH_COMMIT_TWO_OK',
        });

        await context.localBackend.executeAction({
          pluginId: 'cloud',
          actionId: 'cloud.sync_down',
          actionOwner: 'application',
          inputs: {
            instance_id: requireCloudInstanceId(cloudLink),
            session_id: sessionId,
            workspace_dir: context.workspaceDir,
          },
        });

        expect(
          execFileSync('git', ['show', `cloud/${token}/committed:b.txt`], {
            cwd: context.workspaceDir,
            encoding: 'utf8',
          }),
        ).toBe('cloud-b2\n');
        expect(
          execFileSync(
            'git',
            ['show', `refs/cloud-agent/${token}/cloud-full-state:a.txt`],
            { cwd: context.workspaceDir, encoding: 'utf8' },
          ),
        ).toBe('local-a\ncloud residual\n');
      },
      TEST_TIMEOUT_MS,
    );

    it(
      'fails local cloud validation when fixture local-stage does not stage the required env file',
      async () => {
        orchestrator = orchestrator || (await startCloudOrchestratorLocal());
        const context = await startProfileScenario({
          scenario: 'working-tree-patch-broken-local-stage',
          orchestrator,
        });
        cleanupFns.push(context.cleanup);

        initializeGitWorkspace(context.workspaceDir);
        commitFiles(
          context.workspaceDir,
          [
            '.gitignore',
            'local.txt',
            '.cloud-agent/cloud-agent.json',
            '.cloud-agent/local-stage',
            '.cloud-agent/install-cloud',
            '.cloud-agent/validate-cloud',
          ],
          'initial workspace',
        );

        const output = runValidateCloudCommandExpectFailure({
          configPath: context.configPath,
          workspaceDir: context.workspaceDir,
        });
        expect(output).toContain('cloud_install_running failed');
      },
      TEST_TIMEOUT_MS,
    );

    it(
      'fails local cloud validation when the fixture validate hook exits non-zero',
      async () => {
        orchestrator = orchestrator || (await startCloudOrchestratorLocal());
        const context = await startProfileScenario({
          scenario: 'working-tree-patch-invalid-validate',
          orchestrator,
        });
        cleanupFns.push(context.cleanup);

        initializeGitWorkspace(context.workspaceDir);
        commitFiles(
          context.workspaceDir,
          [
            '.gitignore',
            'local.txt',
            '.cloud-agent/cloud-agent.json',
            '.cloud-agent/local-stage',
            '.cloud-agent/install-cloud',
            '.cloud-agent/validate-cloud',
          ],
          'initial workspace',
        );

        const output = runValidateCloudCommandExpectFailure({
          configPath: context.configPath,
          workspaceDir: context.workspaceDir,
        });
        expect(output).toContain('cloud_validation_running failed');
        expect(output).toContain('intentional fixture validation failure');
      },
      TEST_TIMEOUT_MS,
    );
  },
);