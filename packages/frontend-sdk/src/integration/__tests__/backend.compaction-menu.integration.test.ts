import path from 'node:path';
import { afterEach, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { findRepoRoot, startBackendServer, type StartedServer } from '../harness';
import menuLabelActions from '../../../../../test/fixture/action-menu-labels.json';

let started: StartedServer | null = null;
afterEach(async () => {
  await started?.stop();
  started = null;
});

it('delivers the renamed compaction action and preserves eligibility through HTTP', async () => {
  const root = findRepoRoot(process.cwd());
  const pluginModule = 'openai_responses_plugins.';
  started = await startBackendServer({
    config: {
      providers: {
        openai: {
          provider: 'openai_responses',
          model: 'gpt-5-mini',
          api_key: 'local-schema-test-no-provider-requests',
          plugins: [
            `${pluginModule}openai_responses_provider.OpenAIResponsesProvider`,
            `${pluginModule}openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension`,
          ],
        },
      },
      plugins: [
        `${pluginModule}openai_responses_native_compaction_app.OpenAIResponsesNativeCompactionAppPlugin`,
      ],
      agents: {
        enabled: { provider: 'openai' },
        disabled: { provider: 'openai', native_compaction_enabled: false },
      },
    },
    env: {
      PYTHONPATH: [
        'core/python', 'application/python', 'plugins/openai_responses/src',
      ].map((part) => path.join(root, part)).join(path.delimiter),
    },
  });
  const backend = new RestAgentBackend({
    transport: new FetchTransport({ baseUrl: started.baseUrl }),
  });
  const expectedLabel = menuLabelActions[0].label;
  const enabled = await backend.createSession({ agentId: 'enabled' });
  const schema = await backend.getSessionApplicationUiSchema(enabled.session.session_id);
  const action: any = schema.find((element: any) =>
    element.id === 'compact_native_history_through_message');
  expect(action).toMatchObject({
    ui_type: 'message_action',
    plugin: 'openai_responses_native_compaction_app',
    label: expectedLabel,
    action_id: 'compact_native_history',
    action_owner: 'application',
    order: 25,
    param_map: { session_id: '$session.session_id', message_index: '$message.index' },
    dialog: { kind: 'confirm', title: expectedLabel },
  });
  const disabled = await backend.createSession({ agentId: 'disabled' });
  expect(await backend.getSessionApplicationUiSchema(disabled.session.session_id))
    .not.toEqual(expect.arrayContaining([
      expect.objectContaining({ id: 'compact_native_history_through_message' }),
    ]));
}, 60000);