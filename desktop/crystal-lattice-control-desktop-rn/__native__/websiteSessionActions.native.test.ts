import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { FetchTransport, RestAgentBackend } from '@crystal-lattice/frontend-sdk';
import { startBackendServer, type StartedServer } from '../../../packages/frontend-sdk/src/integration/harness';

jest.setTimeout(30 * 60_000);

const project = process.cwd();
const repository = path.resolve(project, '../..');
const output = path.join(project, 'artifacts/website-session-actions');
const inputPath = path.join(output, 'active-run.json');
const configPath = path.join(repository, 'landing_page/visual_assets/runtime/session-actions/config.json');
const captureBundleId = 'com.dynamicprogrammingsolutions.crystallatticecontrol.website-capture';
const captureSources = [
  'desktop/crystal-lattice-control-desktop-rn/src/testing/DesktopWebsiteVisualHarness.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/windows/ActionsPopoverView.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/theme/buildDesktopTheme.ts',
  'desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm',
  'desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm',
  'packages/frontend-sdk/src/backend/restBackend.ts',
  'packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx',
  'packages/frontend-rn-components/src/actions/ActionsMenuContent.tsx',
  'plugins/session-title-app/src/session_title_app/__init__.py',
  'plugins/generate-title-app/src/generate_title_app/__init__.py',
  'plugins/summarize-range-app/src/summarize_range_app/__init__.py',
];
const mappings = [
  { package: 'session-title-app', plugin: 'session_title', id: 'edit_title_from_view', label: 'Edit title', actionId: 'set_session_title', order: 15 },
  { package: 'generate-title-app', plugin: 'generate_title', id: 'generate_title_from_view', label: 'Generate title', actionId: 'generate_title_for_session', order: 16 },
  { package: 'summarize-range-app', plugin: 'summarize_range', id: 'summarize_range', label: 'Summarize range', actionId: 'summarize_range', order: 40 },
];

function runNativeCapture(resultPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn('xcodebuild', [
      '-workspace', 'macos/CrystalLatticeControlDesktopRN.xcworkspace',
      '-scheme', 'CrystalLatticeControlDesktopRN-macOS',
      '-configuration', 'Debug',
      '-destination', 'platform=macOS,arch=arm64',
      '-derivedDataPath', 'build/website-session-actions-derived-data',
      '-resultBundlePath', resultPath,
      `CLC_APP_BUNDLE_IDENTIFIER=${captureBundleId}`,
      'test',
      '-only-testing:CrystalLatticeControlDesktopRN-macOSUITests/SessionFiltersPopoverUITests/testWebsiteSessionActionsLight',
      '-only-testing:CrystalLatticeControlDesktopRN-macOSUITests/SessionFiltersPopoverUITests/testWebsiteSessionActionsDark',
    ], {
      cwd: project,
      env: { ...process.env, FORCE_BUNDLING: '1' },
      stdio: 'inherit',
    });
    child.on('error', reject);
    child.on('exit', code => code === 0 ? resolve() : reject(new Error(`Native capture exited ${code}`)));
  });
}

it('captures real plugin contributions through HTTP, the SDK, and the native menu', async () => {
  fs.mkdirSync(output, { recursive: true });
  const lock = fs.openSync(inputPath, 'wx');
  let server: StartedServer | null = null;
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    server = await startBackendServer({
      config,
      cwd: repository,
      startupTimeoutMs: 120_000,
    });
    const backend = new RestAgentBackend({ transport: new FetchTransport({ baseUrl: server.baseUrl }) });
    const { session } = await backend.createSession({ agentId: 'workshop-planner' });
    const sessionId = session.session_id;
    await backend.appendMessage(sessionId, {
      role: 'user',
      content: 'Help me plan a welcoming, hands-on workshop for our community. We have two hours, twenty participants, and a modest budget.',
    });
    await backend.appendMessage(sessionId, {
      role: 'assistant',
      content: '## A workshop everyone can join\n\nStart with a short welcome, then work in small groups on one practical activity. Leave time to share what each group learned.\n\n- **Welcome and introductions:** 15 minutes\n- **Hands-on activity:** 60 minutes\n- **Share and reflect:** 30 minutes\n- **Next steps:** 15 minutes\n\nI can help turn this outline into a checklist for the venue, materials, and invitations.',
    });
    await backend.executeSessionAction({
      sessionId, pluginId: 'session_title', actionId: 'set_session_title',
      actionOwner: 'application',
      inputs: { session_id: sessionId, title: 'Plan a community workshop', subtitle: 'Agenda, materials, and invitations' },
    });
    expect((await backend.getSessionSummary(sessionId)).metadata?.title)
      .toBe('Plan a community workshop');
    const schema = await backend.getSessionApplicationUiSchema(sessionId);
    for (const mapping of mappings) {
      expect(config.plugins).toContain(`path:plugins/${mapping.package}`);
      expect(schema.find(element => element.id === mapping.id)).toMatchObject({
        plugin: mapping.plugin, label: mapping.label, action_id: mapping.actionId,
        ui_type: 'session_action', order: mapping.order,
      });
    }
    const run = {
      baseUrl: server.baseUrl, sessionId, output, captureBundleId, mappings,
      configExcerpt: { plugins: config.plugins },
      configSha256: createHash('sha256').update(fs.readFileSync(configPath)).digest('hex'),
    };
    fs.writeFileSync(lock, JSON.stringify(run, null, 2));
    fs.writeFileSync(path.join(output, 'contract.json'), JSON.stringify({
      configExcerpt: run.configExcerpt, configSha256: run.configSha256,
      mappings, schema, sessionId,
      sourceHashes: Object.fromEntries(captureSources.map(file => [
        file, createHash('sha256').update(fs.readFileSync(path.join(repository, file))).digest('hex'),
      ])),
    }, null, 2));
    const resultPath = path.join(output, `capture-${Date.now()}.xcresult`);
    await runNativeCapture(resultPath);
    const exported = `${resultPath}-attachments`;
    execFileSync('xcrun', ['xcresulttool', 'export', 'attachments',
      '--path', resultPath, '--output-path', exported], { stdio: 'inherit' });
    const details: Array<{ attachments: Array<{ suggestedHumanReadableName: string; exportedFileName: string }> }> =
      JSON.parse(fs.readFileSync(path.join(exported, 'manifest.json'), 'utf8'));
    const attachments = details.flatMap(testCase => testCase.attachments);
    for (const theme of ['light', 'dark']) {
      for (const kind of ['window', 'popover', 'geometry']) {
        const name = `${theme}-${kind}`;
        const matching = attachments.filter(item => item.suggestedHumanReadableName.startsWith(`${name}.`)
          || item.suggestedHumanReadableName.startsWith(`${name}_`)
          || item.suggestedHumanReadableName === name);
        expect(matching).toHaveLength(1);
        fs.copyFileSync(path.join(exported, matching[0].exportedFileName),
          path.join(output, `${name}.${kind === 'geometry' ? 'json' : 'png'}`));
      }
      const geometry = JSON.parse(fs.readFileSync(path.join(output, `${theme}-geometry.json`), 'utf8'));
      expect(geometry.rows.map((row: { id: string }) => row.id)).toEqual(mappings.map(row => row.id));
      for (const row of geometry.rows) {
        expect(row.frame.width).toBeGreaterThan(0);
        expect(row.frame.height).toBeGreaterThan(0);
      }
      expect(fs.statSync(path.join(output, `${theme}-window.png`)).size).toBeGreaterThan(0);
      expect(fs.statSync(path.join(output, `${theme}-popover.png`)).size).toBeGreaterThan(0);
    }
  } finally {
    await server?.stop();
    fs.closeSync(lock);
    fs.unlinkSync(inputPath);
  }
});