import fs from 'node:fs';
import path from 'node:path';

import { afterEach, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { findRepoRoot, startBackendServer, type StartedServer } from '../harness';

describe('canonical website runtime UI against a real backend', () => {
  let started: StartedServer | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('serves the promoted plugin action and settings contract through RestAgentBackend', async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const configPath = path.join(
      repoRoot,
      'landing_page',
      'visual_assets',
      'runtime',
      'mobile-workbench',
      'config.json',
    );
    const fixturePath = path.join(
      repoRoot,
      'mobile',
      'crystal-lattice-control-rn',
      'src',
      'testing',
      'fixtures',
      'websiteRuntimeUi.json',
    );
    const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
    const pluginSourceRoots = [
      'plugins/feature-request-options/src',
      'plugins/session-actions-app/src',
      'plugins/session-title-app/src',
      'plugins/generate-title-app/src',
      'plugins/summarize-range-app/src',
      'plugins/openai_responses/src',
    ].map((relative) => path.join(repoRoot, relative));

    started = await startBackendServer({
      config: {},
      configPath,
      startupTimeoutMs: 30000,
      env: {
        OPENAI_API_KEY: 'website-runtime-integration-not-used',
        SESSION_RUNTIME_DIR: path.dirname(configPath),
        PYTHONPATH: [
          path.join(repoRoot, 'core', 'python'),
          path.join(repoRoot, 'application', 'python'),
          ...pluginSourceRoots,
        ].join(path.delimiter),
      },
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });

    const created = await backend.createSession({ agentId: 'codex-openai' });
    const sessionId = created.session.session_id;
    const applicationUi = await backend.getSessionApplicationUiSchema(sessionId);
    const sessionUi = await backend.getSessionUiSchema(sessionId);

    const applicationById = new Map(
      applicationUi.map((element: any) => [element.id, element]),
    );
    for (const expected of fixture.session_application_ui_schema) {
      if (!['session_action', 'message_action'].includes(expected.ui_type)) {
        continue;
      }
      const actual: any = applicationById.get(expected.id);
      expect(actual, `missing application UI element ${expected.id}`).toBeTruthy();
      expect(actual.label).toBe(expected.label);
      expect(actual.order).toBe(expected.order);
      expect(actual.plugin).toBe(expected.plugin);
      expect(actual.action_id).toBe(expected.action_id);
      expect(actual.action_owner).toBe(expected.action_owner);
    }

    const sessionByKey = new Map(
      sessionUi
        .filter((element: any) => typeof element.key === 'string')
        .map((element: any) => [element.key, element]),
    );
    for (const expected of fixture.session_ui_schema) {
      const actual: any = sessionByKey.get(expected.key);
      expect(actual, `missing session setting ${expected.key}`).toBeTruthy();
      expect(actual.label).toBe(expected.label);
      if (expected.key !== 'model') {
        expect(actual.type).toBe(expected.type);
      }
    }
  }, 60000);
});