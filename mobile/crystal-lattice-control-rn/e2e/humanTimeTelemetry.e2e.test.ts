/// <reference types="detox" />

import { expect as jestExpect } from '@jest/globals';
import { execFile } from 'node:child_process';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import {
  FetchTransport,
  RestAgentBackend,
} from '@crystal-lattice/frontend-sdk';

import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';

// This suite proves the COLLECTION side of human time telemetry: foreground
// time with a real session open reaches the real duration-tracking plugin's
// store. The
// transport → server → plugin → surfacing chain from stored entries is
// proven by the jest integration tier
// (__integration__/humanTimeSpanUpload.realBackend.integration.test.ts);
// the two layers meet at the stored span rows this test asserts.

// The real app connects to the host: iOS simulators reach the host via
// 127.0.0.1; Android emulators via the 10.0.2.2 alias.
function hostForPlatform(): string {
  return device.getPlatform() === 'android' ? '10.0.2.2' : '127.0.0.1';
}

function pythonBin(): string {
  const repoVenv = path.join(
    fs.realpathSync(process.cwd()),
    '../../.venv/bin/python',
  );
  return process.env.PYTHON || (fs.existsSync(repoVenv) ? repoVenv : 'python');
}

interface StoredSpanRow {
  session_id: string | null;
  duration_ms: number;
}

async function settleAfterModalTransition(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 600));
}

async function openSessionFromList(rowId: string): Promise<void> {
  await element(by.id('sessions-list')).swipe('up', 'slow', 0.4);
  await element(by.id('sessions-list')).scrollTo('top');
  await waitFor(element(by.id(rowId))).toBeVisible().withTimeout(10000);
  await element(by.id(rowId)).tap();
}

function queryStoredSpans(dbPath: string): Promise<StoredSpanRow[]> {
  const script = `import json,sqlite3;conn=sqlite3.connect(${JSON.stringify(
    dbPath,
  )});rows=conn.execute('select session_id, duration_ms from human_time_spans').fetchall();print(json.dumps([{'session_id': r[0], 'duration_ms': r[1]} for r in rows]))`;
  return new Promise((resolve, reject) => {
    execFile(pythonBin(), ['-c', script], (error, stdout) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(JSON.parse(String(stdout)));
    });
  });
}

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== 'android') return;
  try {
    await system.element(by.system.label('Wait')).tap();
  } catch {
    // Some emulator images surface a transient system-process ANR dialog.
  }
  try {
    await system.element(by.system.label('Got it')).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function launchRealApp(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: true,
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id('home-tab'))).toBeVisible().withTimeout(30000);
}

async function connectToServer(port: number): Promise<void> {
  await element(by.id('home-tab')).tap();
  await waitFor(element(by.id('connections-new-connection')))
    .toBeVisible()
    .withTimeout(10000);
  await element(by.id('connections-new-connection')).tap();
  await waitFor(element(by.id('connection-method-manual')))
    .toBeVisible()
    .withTimeout(10000);
  await element(by.id('connection-method-manual')).tap();
  await waitFor(element(by.id('manual-connect-button')))
    .toBeVisible()
    .withTimeout(10000);
  // The inputs carry default values; clear them before typing.
  await element(by.id('manual-host-input')).clearText();
  await element(by.id('manual-host-input')).typeText(hostForPlatform());
  await element(by.id('manual-port-input')).clearText();
  await element(by.id('manual-port-input')).typeText(String(port));
  // A connected production app polls continuously (sessions, request
  // statuses, events), so Detox's idle-based synchronization never sees a
  // quiet moment once the backend connects — the connect tap itself would
  // block forever in its post-action idle wait. The harness-based suites
  // never hit this because they do not connect a real backend; drive the
  // connected app with synchronization disabled.
  await device.disableSynchronization();
  await element(by.id('manual-connect-button')).tap();
  await waitFor(element(by.id('home-tab'))).toBeVisible().withTimeout(30000);
  await element(by.id('home-tab')).tap();
  await waitFor(element(by.id('home-menu'))).toBeVisible().withTimeout(10000);
}

async function enableTimeTracking(): Promise<void> {
  await element(by.id('home-menu')).tap();
  await waitFor(element(by.id('home-menu-global-settings')))
    .toBeVisible()
    .withTimeout(10000);
  // With synchronization disabled, taps fire immediately; iOS drops
  // touches that land while a modal presentation is still animating, so
  // let the menu's fade-in settle before tapping inside it.
  await settleAfterModalTransition();
  await element(by.id('home-menu-global-settings')).tap();
  await waitFor(element(by.id('global-settings-modal')))
    .toBeVisible()
    .withTimeout(10000);
  await settleAfterModalTransition();
  // The Time tracking row sits below the fold on small screens; scroll
  // the settings panel until the toggle is visible.
  let toggleVisible = false;
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      await waitFor(element(by.id('global-settings-time-tracking-toggle')))
        .toBeVisible()
        .withTimeout(2000);
      toggleVisible = true;
      break;
    } catch {
      await element(by.id('global-settings-scroll')).swipe('up', 'fast', 0.4);
    }
  }
  if (!toggleVisible) {
    throw new Error('Time tracking toggle never became visible');
  }
  await element(by.id('global-settings-time-tracking-toggle')).tap();
  await element(by.id('global-settings-modal-close')).tap();
  await settleAfterModalTransition();
}

function listSessionIds(sessionsRoot: string): string[] {
  return fs
    .readdirSync(sessionsRoot)
    .filter(
      (name) =>
        name.endsWith('.json') && !name.endsWith('.selected.json'),
    )
    .map((name) => name.replace(/\.json$/, ''));
}

describe('mobile human time collection (real app + real server)', () => {
  let server: StartedServer | null = null;
  let workspace: string | null = null;
  const seededSessionIds = new Set<string>();

  beforeAll(async () => {
    // A dedicated workspace keeps the recorded spans and the duration store
    // hermetic per run; the config references it through env placeholders.
    workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'clc-human-time-e2e-'));
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
            duration_tracking_db_path: '${env:TEST_WORKSPACE}/human_time.sqlite',
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
      env: {
        TEST_WORKSPACE: workspace,
      },
    });
    const setupBackend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    for (let index = 0; index < 12; index += 1) {
      const created = await setupBackend.createSession({ agentId: 'default' });
      seededSessionIds.add(created.session.session_id);
    }
  });

  afterAll(async () => {
    if (server) {
      await server.stop();
      server = null;
    }
  });

  it('stores foreground time for a real open session', async () => {
    await launchRealApp();
    await connectToServer(server!.port);
    await enableTimeTracking();

    // Create a session through the production UI and open its chat.
    await element(by.id('sessions-tab')).tap();
    await waitFor(element(by.id('sessions-header-action-new-session')))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id('sessions-header-action-new-session')).tap();
    await waitFor(element(by.id('new-session-agent-default')))
      .toBeVisible()
      .withTimeout(30000);
    await settleAfterModalTransition();
    await element(by.id('new-session-agent-default')).tap();
    await waitFor(element(by.id('message-composer-input')))
      .toBeVisible()
      .withTimeout(30000);
    await settleAfterModalTransition();

    const sessionIds = listSessionIds(server!.sessionsRoot).filter(
      (sessionId) => !seededSessionIds.has(sessionId),
    );
    jestExpect(sessionIds).toHaveLength(1);
    const rowId = `session-row-${sessionIds[0]}`;

    // The span starts when the session becomes the foreground Messages
    // surface; typing and sending do not drive collection.
    await element(by.id('message-composer-input')).typeText('hello human time');

    // The multiline iOS keyboard covers the side-mounted Send button.
    // Navigate out and back through the production UI to blur the composer
    // while preserving its draft, then send with the keyboard dismissed.
    await element(by.id('messages-back-to-sessions')).tap();
    await waitFor(element(by.id('sessions-header-action-refresh')))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id('sessions-header-action-refresh')).tap();
    await waitFor(element(by.id(rowId))).toBeVisible().withTimeout(30000);
    await openSessionFromList(rowId);
    await waitFor(element(by.id('message-composer-input')))
      .toHaveText('hello human time')
      .withTimeout(30000);
    await element(by.id('composer-send')).tap();

    // Leaving Messages closes the foreground-session span.
    await element(by.id('messages-back-to-sessions')).tap();
    await waitFor(element(by.id(rowId))).toBeVisible().withTimeout(30000);

    // The close debounce and upload do not require an inactivity wait.
    await new Promise((resolve) => setTimeout(resolve, 5_000));

    // The stored rows are the touch point with the jest integration tier:
    // real UI activity reached the real plugin's store.
    const rows = await queryStoredSpans(
      path.join(workspace!, 'human_time.sqlite'),
    );
    const sessionRows = rows.filter(
      (row) => row.session_id !== null && row.duration_ms > 0,
    );
    jestExpect(sessionRows.length).toBeGreaterThan(0);
    for (const row of sessionRows) {
      jestExpect(row.session_id).toBe(sessionIds[0]);
    }
  }, 600_000);
});