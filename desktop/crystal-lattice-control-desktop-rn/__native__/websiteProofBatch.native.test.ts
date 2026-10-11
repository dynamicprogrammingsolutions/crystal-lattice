import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { FetchTransport, RestAgentBackend } from '@crystal-lattice/frontend-sdk';
import { startBackendServer, type StartedServer } from '../../../packages/frontend-sdk/src/integration/harness';

jest.setTimeout(60 * 60_000);
const project = process.cwd();
const repository = path.resolve(project, '../..');
const output = path.join(project, 'artifacts/website-proof-batch');
const inputPath = path.join(output, 'active-run.json');
const bundleId = 'com.dynamicprogrammingsolutions.crystallatticecontrol.website-capture';
const configRoot = path.join(repository, 'landing_page/visual_assets/runtime');
const hash = (file: string) => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const read = (file: string) => JSON.parse(fs.readFileSync(file, 'utf8'));
const sourceFiles = [
  'desktop/crystal-lattice-control-desktop-rn/src/testing/DesktopWebsiteVisualHarness.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/windows/ActionsPopoverView.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/windows/ActionDisplayWindow.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/ui/DesktopGlobalDisplayLayer.tsx',
  'desktop/crystal-lattice-control-desktop-rn/src/theme/buildDesktopTheme.ts',
  'desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm',
  'desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm',
  'desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOSUITests/SessionFiltersPopoverUITests.swift',
  'desktop/crystal-lattice-control-desktop-rn/__native__/websiteProofBatch.native.test.ts',
  'packages/frontend-sdk/src/backend/restBackend.ts',
  'packages/frontend-rn-components/src/actions/ActionsMenuContent.tsx',
  'packages/frontend-rn-components/src/actions/SessionListActionsBar.tsx',
  'plugins/generate-title-app/src/generate_title_app/__init__.py',
  'plugins/session-title-app/src/session_title_app/__init__.py',
  'plugins/session-actions-app/src/session_actions_app/__init__.py',
  'plugins/summarize-range-app/src/summarize_range_app/__init__.py',
  'plugins/message-export-actions/src/message_export_actions/__init__.py',
  'plugins/session-pinned-app/src/session_pinned_app/__init__.py',
  'plugins/session-archive-app/src/session_archive_app/__init__.py',
  'plugins/session-status-app/src/session_status_app/__init__.py',
  'landing_page/visual_assets/runtime/proof-batch/codex-default-beginning.md',
  'landing_page/visual_assets/runtime/proof-batch/codex-default-source.json',
  'landing_page/visual_assets/runtime/proof-batch/fixture-plugin/src/website_report_fixture/__init__.py',
  'landing_page/visual_assets/runtime/proof-batch/fixture-plugin/src/website_report_fixture/reports.json',
];
const request = 'Help me plan a welcoming, hands-on workshop for our community. We have two hours, twenty participants, and a modest budget.';
const answer = '## A workshop everyone can join\n\nStart with a short welcome, then work in small groups on one practical activity. Leave time to share what each group learned.\n\n- **Welcome and introductions:** 15 minutes\n- **Hands-on activity:** 60 minutes\n- **Share and reflect:** 30 minutes\n- **Next steps:** 15 minutes\n\nI can help turn this outline into a checklist for the venue, materials, and invitations.';
const mappings = {
  'session-actions': [
    { package: 'session-title-app', plugin: 'session_title', id: 'edit_title_from_view', label: 'Edit title', actionId: 'set_session_title' },
    { package: 'generate-title-app', plugin: 'generate_title', id: 'generate_title_from_view', label: 'Generate title', actionId: 'generate_title_for_session' },
    { package: 'summarize-range-app', plugin: 'summarize_range', id: 'summarize_range', label: 'Summarize range', actionId: 'summarize_range' },
  ],
  'message-actions': [
    { package: 'session-actions-app', plugin: 'session_actions', id: 'fork_session_at_message', label: 'Fork here', actionId: 'fork_session_at' },
    { package: 'summarize-range-app', plugin: 'summarize_range', id: 'summarize_before_message', label: 'Summarize messages up to here', actionId: 'summarize_range' },
    { package: 'message-export-actions', plugin: 'message_share_as_pdf', id: 'message_share_as_pdf', label: 'Share as PDF', actionId: 'share_as_pdf' },
    { package: 'message-export-actions', plugin: 'message_share_as_markdown', id: 'message_share_as_markdown', label: 'Share as Markdown', actionId: 'share_as_markdown' },
  ],
  'session-list': [
    { package: 'session-pinned-app', plugin: 'session_pinned', id: 'toggle_session_pinned', label: 'Pin/unpin session', actionId: 'toggle_session_pinned' },
    { package: 'session-archive-app', plugin: 'session_archive', id: 'toggle_session_archived', label: 'Archive/restore session', actionId: 'toggle_session_archived' },
    { package: 'session-status-app', plugin: 'session_status', id: 'set_session_status', label: 'Set status', actionId: 'set_session_status' },
  ],
};
const reportActions = [
  { name: 'compiled', plugin: 'system_message', id: 'show_compiled_system_message', actionId: 'show_compiled_system_message', owner: 'feature' },
  { name: 'usage-overview', plugin: 'website_report_fixture', id: 'website_show_usage', actionId: 'show_illustrative_usage', owner: 'application' },
];

async function seed(backend: RestAgentBackend, title = 'Plan a community workshop', metadata = {}) {
  const { session } = await backend.createSession({ agentId: 'workshop-planner' });
  await backend.appendMessage(session.session_id, { role: 'user', content: request });
  await backend.appendMessage(session.session_id, { role: 'assistant', content: answer, metadata });
  await backend.executeSessionAction({
    sessionId: session.session_id, pluginId: 'session_title', actionId: 'set_session_title',
    actionOwner: 'application', inputs: { session_id: session.session_id, title, subtitle: 'Agenda, materials, and invitations' },
  });
  return session.session_id;
}

it(process.env.CLC_PROOF_BATCH_CONTRACT_ONLY === '1'
  ? 'verifies all proof contracts through public HTTP and the production SDK'
  : 'captures the plugin menus, Codex instructions, and illustrative usage through HTTP, SDK, and native UI', async () => {
  fs.mkdirSync(output, { recursive: true });
  const lock = fs.openSync(inputPath, 'wx');
  const servers: StartedServer[] = [];
  const scenes: any[] = [];
  const runtime = fs.mkdtempSync(path.join(output, 'report-data-'));
  try {
    const reportFixture = read(path.join(configRoot, 'proof-batch/fixture-plugin/src/website_report_fixture/reports.json'));
    async function start(file: string) {
      const config = read(path.join(configRoot, file));
      const server = await startBackendServer({
        config, cwd: repository,
        env: { CAPTURE_DATA_DIR: runtime, CRYSTAL_DATA_DIR: runtime },
        startupTimeoutMs: 180_000,
      });
      servers.push(server);
      return { config, server, backend: new RestAgentBackend({ transport: new FetchTransport({ baseUrl: server.baseUrl }) }), file };
    }
    for (const [name, file] of [
      ['session-actions', 'session-actions/config.json'],
      ['message-actions', 'proof-batch/message-actions.json'],
      ['session-list', 'proof-batch/session-list.json'],
    ]) {
      const { config, server, backend } = await start(file);
      const sessionId = await seed(backend, name === 'session-list' ? 'Prepare the venue' : undefined);
      if (name === 'session-list') {
        await backend.executeSessionAction({
          sessionId, pluginId: 'session_pinned', actionId: 'toggle_session_pinned',
          actionOwner: 'application', inputs: { session_id: sessionId },
        });
        for (const [title, status] of [['Invite the community', 'in_progress'], ['Confirm the materials', 'done']]) {
          const id = await seed(backend, title);
          await backend.executeSessionAction({
            sessionId: id, pluginId: 'session_status', actionId: 'set_session_status',
            actionOwner: 'application', inputs: { session_id: id, status },
          });
        }
      }
      const schema = await backend.getSessionApplicationUiSchema(sessionId);
      const rows = mappings[name as keyof typeof mappings];
      const uiType = name === 'message-actions' ? 'message_action' : name === 'session-list' ? 'session_list_action' : 'session_action';
      for (const row of rows) {
        expect(config.plugins).toContain(`path:plugins/${row.package}`);
        expect(schema.find(item => item.id === row.id && item.ui_type === uiType)).toMatchObject({
          plugin: row.plugin, label: row.label, action_id: row.actionId,
        });
      }
      if (name === 'session-actions') expect(schema.find(row => row.id === 'generate_title_from_view')?.icon).toBe('zap');
      if (name === 'message-actions') {
        expect(schema.find(row => row.id === 'fork_session_at_message')?.param_map?.index).toBe('$message.index');
        expect(schema.find(row => row.id === 'summarize_before_message')?.param_map?.end).toBe('$message.index');
        for (const id of ['message_share_as_pdf', 'message_share_as_markdown']) {
          expect(schema.find(row => row.id === id)?.param_map?.message_index).toBe('$message.index');
        }
      }
      const packages = [...new Set(rows.map(row => `path:plugins/${row.package}`))];
      const list = name === 'session-list' ? await backend.listSessions({ limit: 10 }) : [];
      if (name === 'session-list') {
        expect(list).toHaveLength(3);
        expect(list.find(row => row.session_id === sessionId)?.metadata?.pinned).toBe(true);
        expect(list.some(row => row.metadata?.status === 'in_progress')).toBe(true);
        expect(list.some(row => row.metadata?.status === 'done')).toBe(true);
      }
      scenes.push({
        name, baseUrl: server.baseUrl, sessionId, kind: name === 'session-list' ? 'session-list' : 'session-actions',
        mappings: rows, schema, uiType, messageIndex: 1, list,
        configExcerpt: { plugins: packages }, fullConfigPlugins: config.plugins,
        configFile: `landing_page/visual_assets/runtime/${file}`,
        configSha256: hash(path.join(configRoot, file)),
      });
    }
    const { server, backend, config } = await start('proof-batch/config.json');
    const sessionId = await seed(backend, 'Inspect Codex instructions');
    const schema = [
      ...await backend.getSessionUiSchema(sessionId),
      ...await backend.getSessionApplicationUiSchema(sessionId),
    ];
    for (const action of reportActions) {
      expect(schema.find(row => row.id === action.id)).toMatchObject({ plugin: action.plugin, action_id: action.actionId });
      const response = await backend.executeSessionAction({
        sessionId, pluginId: action.plugin, actionId: action.actionId,
        actionOwner: action.owner, inputs: { session_id: sessionId },
      });
      expect(response).toHaveProperty('result.display.body');
      if (action.name === 'compiled') {
        const beginning = fs.readFileSync(path.join(configRoot, 'proof-batch/codex-default-beginning.md'), 'utf8').trim();
        expect(response.result.display?.body.trim()).toBe(beginning);
        expect(response.result.display?.body).not.toContain('{{CODEX_DEFAULT_BEGINNING}}');
      }
      if (action.name === 'usage-overview') {
        expect(response.result.illustrative_data).toEqual(reportFixture);
        expect(response.result.metrics).toMatchObject({
          estimated_total_usd: '220.00', percentage_point_change: 40,
          weekly_capacity_assumption_usd: '550.00', days_since_reset: 3,
        });
        expect(response.result.display?.body).toContain('| Day | claude | zai |');
        expect(response.result.display?.body).toContain('since reset');
        expect(response.result.display?.body).toContain('0% → 40%');
        expect(response.result.display?.body).toContain('$220.00');
      }
      scenes.push({
        name: action.name, baseUrl: server.baseUrl, sessionId, kind: 'session-actions',
        reportAction: action, schema, response, fullConfigPlugins: config.plugins,
        configFile: 'landing_page/visual_assets/runtime/proof-batch/config.json',
      });
    }
    const sourceHashes = Object.fromEntries([...sourceFiles, ...new Set(scenes.map(scene => scene.configFile))]
      .map(file => [file, hash(path.join(repository, file))]));
    for (const scene of scenes) {
      const directory = path.join(output, scene.name);
      fs.mkdirSync(directory, { recursive: true });
      fs.writeFileSync(path.join(directory, 'contract.json'), JSON.stringify({ ...scene, sourceHashes }, null, 2));
    }
    const run = { captureBundleId: bundleId, scenes };
    fs.writeFileSync(lock, JSON.stringify(run, null, 2));
    fs.writeFileSync(path.join(output, 'contract.json'), JSON.stringify({
      captureReference: reportFixture.chatgpt.captured_at, sourceHashes, scenes, reportFixture,
    }, null, 2));
    if (process.env.CLC_PROOF_BATCH_CONTRACT_ONLY === '1') return;
    const result = path.join(output, `capture-${Date.now()}.xcresult`);
    await new Promise<void>((resolve, reject) => {
      const child = spawn('xcodebuild', [
        '-workspace', 'macos/CrystalLatticeControlDesktopRN.xcworkspace',
        '-scheme', 'CrystalLatticeControlDesktopRN-macOS',
        '-configuration', 'Debug', '-destination', 'platform=macOS,arch=arm64',
        '-derivedDataPath', 'build/website-session-actions-derived-data',
        '-resultBundlePath', result, `CLC_APP_BUNDLE_IDENTIFIER=${bundleId}`, 'test',
        '-only-testing:CrystalLatticeControlDesktopRN-macOSUITests/SessionFiltersPopoverUITests/testWebsiteProofBatch',
      ], { cwd: project, env: { ...process.env, FORCE_BUNDLING: '1' }, stdio: 'inherit' });
      child.on('error', reject);
      child.on('exit', code => code === 0 ? resolve() : reject(new Error(`Native batch exited ${code}`)));
    });
    const exported = `${result}-attachments`;
    execFileSync('xcrun', ['xcresulttool', 'export', 'attachments', '--path', result, '--output-path', exported], { stdio: 'inherit' });
    const attachments = read(path.join(exported, 'manifest.json')).flatMap((item: any) => item.attachments);
    for (const scene of scenes) for (const theme of ['light', 'dark']) {
      for (const kind of ['window', scene.reportAction ? 'report' : 'popover', 'geometry',
        ...(scene.reportAction ? ['conversation', 'report-compact', 'geometry-compact'] : [])]) {
        const prefix = `${scene.name}-${theme}-${kind}`;
        const matches = attachments.filter((item: any) => item.suggestedHumanReadableName.startsWith(`${prefix}.`)
          || item.suggestedHumanReadableName.startsWith(`${prefix}_`) || item.suggestedHumanReadableName === prefix);
        expect(matches).toHaveLength(1);
        fs.copyFileSync(path.join(exported, matches[0].exportedFileName),
          path.join(output, `${prefix}.${kind.startsWith('geometry') ? 'json' : 'png'}`));
        fs.copyFileSync(path.join(exported, matches[0].exportedFileName),
          path.join(output, scene.name, `${theme}-${kind}.${kind.startsWith('geometry') ? 'json' : 'png'}`));
      }
    }
    const legacy = path.join(project, 'artifacts/website-session-actions');
    fs.mkdirSync(legacy, { recursive: true });
    for (const filename of ['contract.json', 'light-window.png', 'light-popover.png', 'light-geometry.json', 'dark-window.png', 'dark-popover.png', 'dark-geometry.json']) {
      fs.copyFileSync(path.join(output, 'session-actions', filename), path.join(legacy, filename));
    }
  } finally {
    await Promise.all(servers.map(server => server.stop()));
    fs.closeSync(lock);
    fs.unlinkSync(inputPath);
  }
});