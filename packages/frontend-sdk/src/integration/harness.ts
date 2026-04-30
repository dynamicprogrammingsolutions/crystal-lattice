import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';

import type { Transport } from '../transport/transport';

export async function waitFor(condition: () => boolean, options?: { timeoutMs?: number; intervalMs?: number }): Promise<void> {
  const timeoutMs = options?.timeoutMs ?? 5000;
  const intervalMs = options?.intervalMs ?? 50;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    if (condition()) {
      return;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }

  throw new Error('waitFor: condition not met before timeout');
}

export async function waitForAsync(
  condition: () => Promise<boolean>,
  options?: { timeoutMs?: number; intervalMs?: number },
): Promise<void> {
  const timeoutMs = options?.timeoutMs ?? 5000;
  const intervalMs = options?.intervalMs ?? 50;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    if (await condition()) {
      return;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }

  throw new Error('waitForAsync: condition not met before timeout');
}

export async function getFreePort(): Promise<number> {
  return await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      server.close(() => {
        if (!addr || typeof addr === 'string') {
          reject(new Error('Failed to determine free port'));
          return;
        }
        resolve(addr.port);
      });
    });
  });
}

function findRepoRoot(fromDir: string): string {
  let current = fromDir;
  for (let i = 0; i < 10; i += 1) {
    const candidate = path.join(current, 'core', 'python');
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

export interface StartedServer {
  baseUrl: string;
  port: number;
  configPath: string;
  sessionsRoot: string;
  stdout: string[];
  stop: () => Promise<void>;
}

export async function startBackendServer(options: {
  config: Record<string, any>;
  enableTestControl?: boolean;
  env?: Record<string, string>;
  configPath?: string;
  sessionsRoot?: string;
  port?: number;
  sessionSaveDelayMs?: number;
  checkpointDelayMs?: number;
  eventStoreOptions?: {
    maxEventsGlobal?: number;
    maxEventAgeSeconds?: number;
  };
}): Promise<StartedServer> {
  const repoRoot = findRepoRoot(process.cwd());
  const runnerPath = path.join(repoRoot, 'scripts', 'run_backend_server_for_ts_integration_tests.py');
  if (!fs.existsSync(runnerPath)) {
    throw new Error(`Missing runner script: ${runnerPath}`);
  }

  const tmpRoot =
    options.configPath && options.sessionsRoot
      ? null
      : fs.mkdtempSync(path.join(os.tmpdir(), 'cl-backend-integration-'));
  const sessionsRoot = options.sessionsRoot ?? path.join(tmpRoot!, 'sessions');
  fs.mkdirSync(sessionsRoot, { recursive: true });
  const configPath = options.configPath ?? path.join(tmpRoot!, 'config.json');
  if (!options.configPath) {
    fs.writeFileSync(configPath, JSON.stringify(options.config, null, 2), 'utf8');
  }

  const port = options.port ?? await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;

  const python = process.env.PYTHON || 'python';
  const args = [runnerPath, '--config', configPath, '--sessions', sessionsRoot, '--port', String(port)];
  if (typeof options.eventStoreOptions?.maxEventsGlobal === 'number') {
    args.push('--max-events-global', String(options.eventStoreOptions.maxEventsGlobal));
  }
  if (typeof options.eventStoreOptions?.maxEventAgeSeconds === 'number') {
    args.push('--max-event-age-seconds', String(options.eventStoreOptions.maxEventAgeSeconds));
  }
  if (typeof options.sessionSaveDelayMs === 'number' && options.sessionSaveDelayMs > 0) {
    args.push('--session-save-delay-ms', String(options.sessionSaveDelayMs));
  }
  if (typeof options.checkpointDelayMs === 'number' && options.checkpointDelayMs > 0) {
    args.push('--checkpoint-delay-ms', String(options.checkpointDelayMs));
  }
  if (options.enableTestControl) {
    args.push('--enable-test-control');
  }

  const child = spawn(python, args, {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: {
      ...process.env,
      ...(options.env || {}),
      REPO_ROOT: repoRoot,
      BUILTIN_PLUGINS: path.join(repoRoot, 'plugins'),
      PYTHONUNBUFFERED: '1',
    },
  });

  const stdout: string[] = [];
  child.stdout.on('data', (buf) => {
    stdout.push(String(buf));
  });

  // If the backend fails to start, surface stderr to make debugging easier.
  const stderr: string[] = [];
  child.stderr.on('data', (buf) => {
    stderr.push(String(buf));
  });

  // Wait for readiness.
  await (async () => {
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline) {
      try {
        const resp = await fetch(`${baseUrl}/api/hello`);
        if (resp.ok) {
          return;
        }
      } catch {
        // keep trying
      }
      await new Promise((r) => setTimeout(r, 50));
    }
    throw new Error(`Backend did not become ready. Stderr:\n${stderr.join('')}`);
  })();

  async function stop(): Promise<void> {
    if (child.killed) {
      return;
    }
    child.kill('SIGTERM');
    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => {
        child.kill('SIGKILL');
        resolve();
      }, 2000);
      child.on('exit', () => {
        clearTimeout(timeout);
        resolve();
      });
    });
  }

  return {
    baseUrl,
    port,
    configPath,
    sessionsRoot,
    stdout,
    stop,
  };
}

export interface StartedBridge {
  bridgeUrl: string;
  stop: () => Promise<void>;
  suspend?: () => Promise<void>;
  resume?: () => Promise<void>;
}

export interface StartedCloudOrchestrator {
  baseUrl: string;
  port: number;
  dataDir: string;
  stop: () => Promise<void>;
}

async function commandExists(cmd: string, args: string[]): Promise<boolean> {
  return await new Promise<boolean>((resolve) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'ignore'] });
    child.on('error', () => resolve(false));
    child.on('exit', (code) => resolve(code === 0));
  });
}

async function runCommand(options: { cmd: string; args: string[]; cwd: string }): Promise<string> {
  return await new Promise<string>((resolve, reject) => {
    const child = spawn(options.cmd, options.args, {
      cwd: options.cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    child.stdout.on('data', (buf) => {
      out += String(buf);
    });
    child.stderr.on('data', (buf) => {
      out += String(buf);
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) {
        resolve(out);
      } else {
        reject(new Error(`Command failed (${options.cmd} ${options.args.join(' ')}):\n${out}`));
      }
    });
  });
}

export async function startCloudOrchestratorLocal(): Promise<StartedCloudOrchestrator> {
  const repoRoot = findRepoRoot(process.cwd());
  const cwd = path.join(repoRoot, 'cloud-orchestrator');
  const port = await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-orchestrator-'));

  await runCommand({
    cmd: 'docker',
    args: ['build', '-t', 'cloud-agent-runtime:latest', 'runtime/python'],
    cwd,
  });

  const child = spawn('mix', ['run', '--no-halt'], {
    cwd,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: {
      ...process.env,
      PORT: String(port),
      CLOUD_ORCHESTRATOR_RUNNER: 'docker',
      CLOUD_ORCHESTRATOR_PUBLIC_URL: baseUrl,
      CLOUD_ORCHESTRATOR_TOKEN_SECRET: 'integration-token-secret',
      CLOUD_ORCHESTRATOR_DATA_DIR: dataDir,
      CLOUD_ORCHESTRATOR_HOST_DATA_DIR: dataDir,
      PYTHONUNBUFFERED: '1',
    },
  });

  const stderr: string[] = [];
  child.stderr.on('data', (buf) => stderr.push(String(buf)));
  child.stdout.on('data', (buf) => stderr.push(String(buf)));

  await waitForAsync(async () => {
    try {
      const resp = await fetch(`${baseUrl}/health`);
      return resp.ok;
    } catch {
      return false;
    }
  }, { timeoutMs: 60_000, intervalMs: 250 });

  async function stop(): Promise<void> {
    if (!child.killed) {
      child.kill('SIGTERM');
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          child.kill('SIGKILL');
          resolve();
        }, 3000);
        child.on('exit', () => {
          clearTimeout(timeout);
          resolve();
        });
      });
    }

    try {
      const ids = await runCommand({
        cmd: 'docker',
        args: ['ps', '-aq', '--filter', 'name=cloud-agent-inst_'],
        cwd,
      });
      const list = ids.split(/\s+/).filter(Boolean);
      if (list.length > 0) {
        await runCommand({ cmd: 'docker', args: ['rm', '-f', ...list], cwd });
      }
    } catch {
      // Best-effort cleanup only.
    }

    fs.rmSync(dataDir, { recursive: true, force: true });
  }

  child.on('exit', (code) => {
    if (code !== 0 && code !== null) {
      // Keep the buffered output reachable in debugger stacks.
      stderr.push(`cloud orchestrator exited with ${code}`);
    }
  });

  return { baseUrl, port, dataDir, stop };
}

export async function startCloudOrchestratorForE2E(): Promise<StartedCloudOrchestrator> {
  const mode = process.env.CLOUD_ORCHESTRATOR_E2E_MODE || 'local';

  if (mode === 'local') {
    return await startCloudOrchestratorLocal();
  }

  if (mode === 'external') {
    const baseUrl = process.env.CLOUD_ORCHESTRATOR_E2E_URL;
    if (!baseUrl) {
      throw new Error('CLOUD_ORCHESTRATOR_E2E_URL is required when CLOUD_ORCHESTRATOR_E2E_MODE=external');
    }

    await waitForAsync(async () => {
      try {
        const resp = await fetch(`${baseUrl.replace(/\/$/, '')}/health`);
        return resp.ok;
      } catch {
        return false;
      }
    }, { timeoutMs: 60_000, intervalMs: 500 });

    return {
      baseUrl: baseUrl.replace(/\/$/, ''),
      port: 0,
      dataDir: '',
      stop: async () => {},
    };
  }

  if (mode === 'aws-ec2-cloudfront') {
    return await startCloudOrchestratorAwsEc2();
  }

  throw new Error(`Unsupported CLOUD_ORCHESTRATOR_E2E_MODE=${mode}`);
}

async function startCloudOrchestratorAwsEc2(): Promise<StartedCloudOrchestrator> {
  if (process.env.RUN_AWS_CLOUD_ORCHESTRATOR_TESTS !== '1') {
    throw new Error('RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 is required for AWS cloud orchestrator E2E modes');
  }
  process.env.ALLOW_AWS_DEPLOY = '1';

  const repoRoot = findRepoRoot(process.cwd());
  const cwd = path.join(repoRoot, 'cloud-orchestrator');
  const stackName =
    process.env.AWS_STACK_NAME ||
    `crystal-lattice-cloud-orchestrator-e2e-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const region = process.env.AWS_REGION || 'us-east-1';
  const deployDir = path.join(cwd, 'deploy', 'aws-ec2');

  const upOutput = await runCommand({
    cmd: path.join(deployDir, 'up.sh'),
    args: [
      '--profile',
      'secure',
      '--stack-name',
      stackName,
      '--region',
      region,
      '--json',
    ],
    cwd,
  });
  const parsed = parseCloudOrchestratorOutput(upOutput);
  if (parsed.controlToken) {
    process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN = parsed.controlToken;
  }

  async function stop(): Promise<void> {
    await runCommand({
      cmd: path.join(deployDir, 'down.sh'),
      args: ['--profile', 'secure', '--stack-name', stackName, '--region', region],
      cwd,
    });
  }

  return {
    baseUrl: parsed.orchestratorUrl,
    port: 0,
    dataDir: '',
    stop,
  };
}

function parseCloudOrchestratorOutput(output: string): { orchestratorUrl: string; controlToken?: string } {
  const trimmed = output.trim();
  const lines = trimmed.split(/\r?\n/);
  const jsonLine = [...lines].reverse().find((line) => line.trim().startsWith('{'));
  if (jsonLine) {
    const parsed = JSON.parse(jsonLine);
    const orchestratorUrl =
      parsed.cloudOrchestratorUrl || parsed.orchestratorUrl || parsed.cloudFrontUrl || parsed.CloudOrchestratorUrl;
    if (typeof orchestratorUrl === 'string' && orchestratorUrl) {
      return {
        orchestratorUrl,
        controlToken: typeof parsed.controlToken === 'string' ? parsed.controlToken : undefined,
      };
    }
  }

  const match = trimmed.match(/CloudOrchestratorUrl=([^\s]+)/);
  if (match) {
    return { orchestratorUrl: match[1] };
  }

  throw new Error(`Unable to parse CloudOrchestratorUrl from output:\n${output}`);
}

export async function startBridgeDocker(): Promise<StartedBridge> {
  const repoRoot = findRepoRoot(process.cwd());
  const cwd = path.join(repoRoot, 'bridge-elixir');
  const composeFile = 'docker-compose.single-node.yml';

  const hasDockerCompose = await commandExists('docker', ['compose', 'version']);
  const composeCmd = hasDockerCompose ? 'docker' : 'docker-compose';
  const baseArgs = hasDockerCompose ? ['compose'] : [];

  await runCommand({
    cmd: composeCmd,
    args: [...baseArgs, '-f', composeFile, 'up', '-d'],
    cwd,
  });

  const healthUrl = 'http://127.0.0.1:4000/health';
  await waitForAsync(async () => {
    try {
      const resp = await fetch(healthUrl);
      return resp.ok;
    } catch {
      return false;
    }
  }, { timeoutMs: 60_000, intervalMs: 250 });

  async function stop(): Promise<void> {
    await runCommand({
      cmd: composeCmd,
      args: [...baseArgs, '-f', composeFile, 'down', '--remove-orphans', '-v'],
      cwd,
    });
  }

  return {
    bridgeUrl: 'ws://127.0.0.1:4000/ws/websocket',
    stop,
  };
}

export async function startBridgeForE2E(): Promise<StartedBridge> {
  const mode = process.env.BRIDGE_E2E_MODE || 'docker';

  if (mode === 'docker') {
    return await startBridgeDocker();
  }

  if (mode === 'external') {
    const bridgeUrl = process.env.BRIDGE_E2E_URL;
    if (!bridgeUrl) {
      throw new Error('BRIDGE_E2E_URL is required when BRIDGE_E2E_MODE=external');
    }
    return {
      bridgeUrl,
      stop: async () => {},
    };
  }

  if (mode === 'aws-public-task' || mode === 'aws-secure' || mode === 'aws-ec2-secure') {
    return await startBridgeAws(mode);
  }

  throw new Error(`Unsupported BRIDGE_E2E_MODE=${mode}`);
}

async function startBridgeAws(mode: 'aws-public-task' | 'aws-secure' | 'aws-ec2-secure'): Promise<StartedBridge> {
  if (process.env.RUN_AWS_BRIDGE_TESTS !== '1') {
    throw new Error('RUN_AWS_BRIDGE_TESTS=1 is required for AWS bridge E2E modes');
  }
  process.env.ALLOW_AWS_DEPLOY = '1';

  const repoRoot = findRepoRoot(process.cwd());
  const cwd = path.join(repoRoot, 'bridge-elixir');
  const isEc2 = mode === 'aws-ec2-secure';
  const profile = mode === 'aws-public-task' ? 'public-task' : 'secure';
  const stackName =
    process.env.AWS_STACK_NAME ||
    `crystal-lattice-bridge-e2e-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const region = process.env.AWS_REGION || 'us-east-1';
  const deployDir = path.join(cwd, 'deploy', isEc2 ? 'aws-ec2' : 'aws-fargate');
  const script = path.join(deployDir, 'up.sh');
  const upArgs = ['--profile', profile, '--stack-name', stackName, '--region', region, '--json'];

  const upOutput = await runCommand({
    cmd: script,
    args: upArgs,
    cwd,
  });
  const parsed = parseBridgeOutput(upOutput);

  async function stop(): Promise<void> {
    await runCommand({
      cmd: path.join(deployDir, 'down.sh'),
      args: ['--profile', profile, '--stack-name', stackName, '--region', region],
      cwd,
    });
  }

  async function runEc2ContainerCommand(command: string): Promise<void> {
    if (!parsed.instanceId) {
      throw new Error('EC2 bridge instance id was not returned by deployment output');
    }
    const commandId = (
      await runCommand({
        cmd: 'aws',
        args: [
          '--region',
          region,
          'ssm',
          'send-command',
          '--instance-ids',
          parsed.instanceId,
          '--document-name',
          'AWS-RunShellScript',
          '--parameters',
          `commands=["${command}"]`,
          '--query',
          'Command.CommandId',
          '--output',
          'text',
        ],
        cwd,
      })
    ).trim();
    await runCommand({
      cmd: 'aws',
      args: [
        '--region',
        region,
        'ssm',
        'wait',
        'command-executed',
        '--command-id',
        commandId,
        '--instance-id',
        parsed.instanceId,
      ],
      cwd,
    });
  }

  async function suspend(): Promise<void> {
    if (isEc2) {
      await runEc2ContainerCommand('docker stop crystal-lattice-bridge');
      return;
    }
    await runCommand({
      cmd: path.join(deployDir, 'stop.sh'),
      args: ['--profile', profile, '--stack-name', stackName, '--region', region],
      cwd,
    });
  }

  async function resume(): Promise<void> {
    if (isEc2) {
      await runEc2ContainerCommand('docker start crystal-lattice-bridge');
      return;
    }
    await runCommand({
      cmd: path.join(deployDir, 'start.sh'),
      args: ['--profile', profile, '--stack-name', stackName, '--region', region],
      cwd,
    });
  }

  return { bridgeUrl: parsed.bridgeUrl, stop, suspend, resume };
}

function parseBridgeOutput(output: string): { bridgeUrl: string; instanceId?: string } {
  const trimmed = output.trim();
  const lines = trimmed.split(/\r?\n/);
  const jsonLine = [...lines].reverse().find((line) => line.trim().startsWith('{'));
  if (jsonLine) {
    const parsed = JSON.parse(jsonLine);
    const value = parsed.bridgeWebSocketUrl || parsed.BridgeWebSocketUrl;
    if (typeof value === 'string') {
      return {
        bridgeUrl: value,
        instanceId: typeof parsed.instanceId === 'string' ? parsed.instanceId : undefined,
      };
    }
  }

  const match = trimmed.match(/BridgeWebSocketUrl=([^\s]+)/);
  if (match) {
    const instanceMatch = trimmed.match(/InstanceId=([^\s]+)/);
    return { bridgeUrl: match[1], instanceId: instanceMatch?.[1] };
  }

  throw new Error(`Unable to parse BridgeWebSocketUrl from output:\n${output}`);
}

export async function waitForStdoutMatch(options: {
  stdout: string[];
  pattern: RegExp;
  timeoutMs?: number;
}): Promise<RegExpMatchArray> {
  const timeoutMs = options.timeoutMs ?? 30_000;
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const text = options.stdout.join('');
    const match = text.match(options.pattern);
    if (match) {
      return match;
    }
    await new Promise((r) => setTimeout(r, 50));
  }
  throw new Error(`waitForStdoutMatch: pattern not found: ${options.pattern}`);
}

export class TrackingTransport implements Transport {
  private inner: Transport;
  private calls: Array<{ method: string; path: string }> = [];

  constructor(inner: Transport) {
    this.inner = inner;
  }

  getCount(key: { method: string; pathPrefix: string }): number {
    return this.calls.filter(
      (call) => call.method === key.method && call.path.startsWith(key.pathPrefix),
    ).length;
  }

  async request<T = any>(req: {
    method: any;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    this.calls.push({ method: String(req.method), path: req.path.split('?')[0] });
    return await this.inner.request(req);
  }
}

export class Gate {
  private open = true;
  private waiters: Array<() => void> = [];

  close(): void {
    this.open = false;
  }

  release(): void {
    this.open = true;
    const list = this.waiters;
    this.waiters = [];
    for (const fn of list) fn();
  }

  async wait(): Promise<void> {
    if (this.open) {
      return;
    }
    await new Promise<void>((resolve) => {
      this.waiters.push(resolve);
    });
  }
}

export class DelayingTransport implements Transport {
  private inner: Transport;
  private gate: Gate;
  pendingEventsRequests = 0;

  constructor(inner: Transport, gate: Gate) {
    this.inner = inner;
    this.gate = gate;
  }

  async request<T = any>(req: {
    method: any;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }> {
    const isEvents = req.path.startsWith('/events');
    if (!isEvents) {
      return await this.inner.request(req);
    }

    this.pendingEventsRequests += 1;
    try {
      const resp = await this.inner.request<T>(req);
      await this.gate.wait();
      return resp;
    } finally {
      this.pendingEventsRequests -= 1;
    }
  }
}
