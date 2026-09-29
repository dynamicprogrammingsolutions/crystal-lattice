import { execFile, spawn } from 'node:child_process';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { promisify } from 'node:util';

import {
  FetchTransport,
  RestAgentBackend,
} from '@crystal-lattice/frontend-sdk';
import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';

const execFileAsync = promisify(execFile);
const NATIVE_FIXTURE_PATH = '/tmp/clc-human-time-telemetry-native.json';

jest.setTimeout(15 * 60_000);

function pythonBin(): string {
  const repositoryPython = path.resolve(
    process.cwd(),
    '../../.venv/bin/python',
  );
  return (
    process.env.PYTHON ||
    (fs.existsSync(repositoryPython) ? repositoryPython : 'python')
  );
}

async function runXCTest(): Promise<void> {
  const args = [
    '-workspace',
    'macos/CrystalLatticeControlDesktopRN.xcworkspace',
    '-scheme',
    'CrystalLatticeControlDesktopRN-macOS',
    '-configuration',
    'Release',
    '-destination',
    'platform=macOS,arch=arm64',
    'test',
    '-only-testing:CrystalLatticeControlDesktopRN-macOSUITests/HumanTimeTelemetryUITests',
  ];
  await new Promise<void>((resolve, reject) => {
    const child = spawn('xcodebuild', args, {
      cwd: process.cwd(),
      env: {
        ...process.env,
        FORCE_BUNDLING: '1',
      },
      stdio: 'inherit',
    });
    child.on('error', reject);
    child.on('exit', code => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`xcodebuild exited with code ${String(code)}`));
      }
    });
  });
}

interface StoredSpan {
  session_id: string | null;
  duration_ms: number;
}

async function queryStoredSpans(dbPath: string): Promise<StoredSpan[]> {
  const script = [
    'import json, sqlite3, sys',
    'conn = sqlite3.connect(sys.argv[1])',
    "try: rows = conn.execute('select session_id, duration_ms from human_time_spans').fetchall()",
    'except sqlite3.OperationalError: rows = []',
    "print(json.dumps([{'session_id': row[0], 'duration_ms': row[1]} for row in rows]))",
  ].join('\n');
  const result = await execFileAsync(pythonBin(), ['-c', script, dbPath]);
  return JSON.parse(String(result.stdout)) as StoredSpan[];
}

async function waitForStoredSpans(
  dbPath: string,
  sessionId: string,
): Promise<StoredSpan[]> {
  const deadline = Date.now() + 30_000;
  let latest: StoredSpan[] = [];
  while (Date.now() < deadline) {
    latest = await queryStoredSpans(dbPath);
    if (latest.some(row => row.session_id === sessionId && row.duration_ms > 0)) {
      return latest;
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error(
    `Timed out waiting for a session human-time row: ${JSON.stringify(
      latest,
    )}`,
  );
}

describe('macOS human-time collection', () => {
  let server: StartedServer | null = null;

  afterEach(async () => {
    if (server) {
      await server.stop();
      server = null;
    }
    try {
      fs.rmSync(NATIVE_FIXTURE_PATH);
    } catch {}
  });

  it('stores a positive session span from the production UI', async () => {
    const workspace = fs.mkdtempSync(
      path.join(os.tmpdir(), 'clc-desktop-human-time-native-'),
    );
    const dbPath = path.join(workspace, 'human_time.sqlite');
    server = await startBackendServer({
      config: {
        providers: {
          stream: {
            provider: 'deterministic_stream',
            model: 'test-model',
            timeout: 60,
            stream_chunk_count: 3,
            stream_chunk_delay_ms: 0,
            working_directory: '${env:TEST_WORKSPACE}',
            duration_tracking_db_path:
              '${env:TEST_WORKSPACE}/human_time.sqlite',
          },
        },
        agents: {
          default: {
            provider: 'stream',
            working_directory: '${env:TEST_WORKSPACE}',
            allowed_paths: ['${env:TEST_WORKSPACE}'],
          },
        },
        plugins: [
          'plugins.deterministic_stream_provider.DeterministicStreamProvider',
          'path:${env:REPO_ROOT}/plugins/timestamp-extension',
          'path:${env:REPO_ROOT}/plugins/duration-tracking',
        ],
        application: {
          duration_tracking: {
            working_directory: '${env:TEST_WORKSPACE}',
            db_path: '${env:TEST_WORKSPACE}/human_time.sqlite',
          },
        },
      },
      env: { TEST_WORKSPACE: workspace },
      startupTimeoutMs: 30_000,
    });

    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const sessions: string[] = [];
    for (let index = 0; index < 12; index += 1) {
      const created = await backend.createSession({ agentId: 'default' });
      sessions.push(created.session.session_id);
    }
    const targetSessionId = sessions[sessions.length - 1];
    const runId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const connectionId = `human-time-native-${runId}`;
    const sessionSummaries = await backend.listSessions();

    fs.writeFileSync(
      NATIVE_FIXTURE_PATH,
      JSON.stringify({
        runId,
        connection: {
          id: connectionId,
          kind: 'manual',
          name: `Human Time ${runId}`,
          host: '127.0.0.1',
          port: server.port,
          lastUsedAt: Date.now(),
        },
        sessions: sessionSummaries,
        sessionId: targetSessionId,
      }),
    );
    await runXCTest();

    const messages = await backend.listMessages(targetSessionId, {});
    expect(
      messages.messages.some(
        entry =>
          entry.message.role === 'user' &&
          String(entry.message.content).includes('hello desktop human time'),
      ),
    ).toBe(true);

    const rows = await waitForStoredSpans(dbPath, targetSessionId);
    expect(
      rows.some(
        row => row.session_id === targetSessionId && row.duration_ms > 0,
      ),
    ).toBe(true);
  });
});
