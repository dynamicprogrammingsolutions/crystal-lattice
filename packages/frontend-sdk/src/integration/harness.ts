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

  const port = await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;

  const python = process.env.PYTHON || 'python';
  const args = [runnerPath, '--config', configPath, '--sessions', sessionsRoot, '--port', String(port)];
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
    configPath,
    sessionsRoot,
    stdout,
    stop,
  };
}

export interface StartedBridge {
  bridgeUrl: string;
  stop: () => Promise<void>;
}

async function commandExists(cmd: string, args: string[]): Promise<boolean> {
  return await new Promise<boolean>((resolve) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'ignore'] });
    child.on('error', () => resolve(false));
    child.on('exit', (code) => resolve(code === 0));
  });
}

async function runCommand(options: { cmd: string; args: string[]; cwd: string }): Promise<void> {
  await new Promise<void>((resolve, reject) => {
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
        resolve();
      } else {
        reject(new Error(`Command failed (${options.cmd} ${options.args.join(' ')}):\n${out}`));
      }
    });
  });
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
