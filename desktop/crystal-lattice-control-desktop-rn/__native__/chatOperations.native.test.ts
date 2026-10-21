import { execFile, spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { promisify } from 'node:util';
import {
  startAcknowledgementProxy,
  startChatOperationsBackend,
} from '../../../test/fixture/chat-operations/backend';

const execFileAsync = promisify(execFile);
const TEST_BUNDLE_PREFIX =
  'com.dynamicprogrammingsolutions.crystallatticecontrol.chatoperationstests';
const TEST_APP_BUNDLE_ID = `${TEST_BUNDLE_PREFIX}.CrystalLatticeControlDesktopRN-macOS`;
jest.setTimeout(30 * 60_000);

test('chat operations through macOS production UI and real HTTP', async () => {
  const processes = await execFileAsync('ps', ['-ax', '-o', 'command=']);
  const testExecutable = path.resolve(
    'build/chat-operations/Build/Products/Debug/Crystal Lattice Desktop.app/Contents/MacOS/Crystal Lattice Desktop',
  );
  const existing = processes.stdout
    .split('\n')
    .filter(line => line.startsWith(testExecutable));
  if (existing.length > 0) {
    throw new Error(
      `The isolated Chat test application is already running. Close that test instance before rerunning.\n${existing.join(
        '\n',
      )}`,
    );
  }
  const started = await startChatOperationsBackend({ streamChunkCount: 45 });
  const proxy = await startAcknowledgementProxy(started.server, {
    editDelayMs: 15_000,
  });
  const fixturePath = path.resolve('build/chat-operations-fixture.json');
  try {
    proxy.setRule('delay-edit');
    proxy.setSendRules([
      'none',
      'reject-send-after',
      'none',
      'reject-send-before',
    ]);
    const runId = `${Date.now()}`;
    const fixture = {
      runId,
      bundleIdentifier: TEST_APP_BUNDLE_ID,
      connection: {
        id: `chat-operations-${runId}`,
        kind: 'manual',
        name: `Chat operations ${runId}`,
        host: '127.0.0.1',
        port: proxy.port,
        lastUsedAt: Date.now(),
      },
      sessions: await started.backend.listSessions(),
      sessionId: started.sessions[0],
      openSessionIds: started.sessions,
    };
    fs.mkdirSync(path.dirname(fixturePath), { recursive: true });
    fs.writeFileSync(fixturePath, JSON.stringify(fixture));
    await new Promise<void>((resolve, reject) => {
      const child = spawn(
        'xcodebuild',
        [
          '-workspace',
          'macos/CrystalLatticeControlDesktopRN.xcworkspace',
          '-scheme',
          'CrystalLatticeControlDesktopRN-macOS',
          '-configuration',
          'Debug',
          '-destination',
          'platform=macOS,arch=arm64',
          '-derivedDataPath',
          path.resolve('build/chat-operations'),
          `PRODUCT_BUNDLE_IDENTIFIER=${TEST_BUNDLE_PREFIX}.$(TARGET_NAME:rfc1034identifier)`,
          'test',
          '-only-testing:CrystalLatticeControlDesktopRN-macOSUITests/ChatOperationsUITests',
        ],
        {
          cwd: process.cwd(),
          env: {
            ...process.env,
            FORCE_BUNDLING: '1',
            CLC_HUMAN_TIME_NATIVE_FIXTURE_JSON: JSON.stringify(fixture),
          },
          stdio: 'inherit',
        },
      );
      child.on('error', reject);
      child.on('exit', code =>
        code === 0 ? resolve() : reject(new Error(`xcodebuild exited ${code}`)),
      );
    });
    const messages = await started.backend.listMessages(
      started.sessions[0],
      {},
    );
    expect(messages.messages[23].message.content).toMatch(
      /^native desktop edited message /,
    );
    expect(messages.messages[23].message.metadata?.fixture).toBe(23);
    expect(
      messages.messages.filter(
        entry => entry.message.content === 'native uncertain desktop send',
      ),
    ).toHaveLength(1);
    expect(
      messages.messages.some(
        entry => entry.message.content === 'native cancelled desktop draft',
      ),
    ).toBe(false);
  } finally {
    fs.rmSync(fixturePath, { force: true });
    await proxy.stop();
    await started.server.stop();
  }
});
