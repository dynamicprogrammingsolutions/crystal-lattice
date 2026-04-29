import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { afterAll, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import {
  CloudTransport,
  parseCloudConnectionLink,
} from '../../transport/cloudTransport';
import {
  startBackendServer,
  startCloudOrchestratorForE2E,
} from '../harness';

const RUN = process.env.RUN_CLOUD_ORCHESTRATOR_E2E === '1';
const describeIf = RUN ? describe : describe.skip;
const IS_AWS_E2E = (process.env.CLOUD_ORCHESTRATOR_E2E_MODE || '').startsWith('aws-');

const TEST_TIMEOUT_MS = IS_AWS_E2E ? 2_700_000 : 600_000;
const HOOK_TIMEOUT_MS = IS_AWS_E2E ? 900_000 : 60_000;

function localBackendConfig(options: { orchestratorUrl: string; workspaceDir: string }) {
  const cloudAgent: Record<string, any> = {
    orchestrator_url: options.orchestratorUrl,
    workspace_dir: options.workspaceDir,
    cloud_workspace_dir: '/workspace',
  };
  if (process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN) {
    cloudAgent.orchestrator_token = process.env.CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN;
  }

  return {
    providers: {
      test_provider: {
        provider: 'echo_openai_like',
        model: 'test-model',
        timeout: 60,
      },
    },
    plugins: [
      'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
      'plugins.cloud_agent_app_plugin.CloudAgentAppPlugin',
    ],
    agents: {
      default: {
        provider: 'test_provider',
      },
    },
    application: {
      cloud_agent: cloudAgent,
    },
  };
}

describeIf('cloud orchestrator e2e (frontend SDK -> local app action -> orchestrator -> cloud runtime)', () => {
  let stopAll: Array<() => Promise<void>> = [];

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'opens a cloud session through CloudTransport and syncs workspace files back down',
    async () => {
      const orchestrator = await startCloudOrchestratorForE2E();
      stopAll.push(orchestrator.stop);

      const workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-cloud-workspace-'));
      fs.writeFileSync(path.join(workspaceDir, 'local.txt'), 'local file\n', 'utf8');

      const localServer = await startBackendServer({
        config: localBackendConfig({
          orchestratorUrl: orchestrator.baseUrl,
          workspaceDir,
        }),
      });
      stopAll.push(async () => {
        fs.rmSync(workspaceDir, { recursive: true, force: true });
        await localServer.stop();
      });

      const localBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: localServer.baseUrl }),
      });

      const created = await localBackend.createSession({ agentId: 'default' });
      const sessionId = created.session.session_id;
      await localBackend.appendMessage(sessionId, {
        role: 'user',
        content: 'local hello',
      });

      const startResult = await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.start_session_agent',
        actionOwner: 'application',
        inputs: { session_id: sessionId },
      });

      expect(startResult.status).toBe('ok');
      const link = (startResult.result as any).connection_link as string;
      const cloudLink = parseCloudConnectionLink(link);
      expect(cloudLink.sessionId).toBe(sessionId);

      const cloudTransport = new CloudTransport({
        orchestratorUrl: cloudLink.orchestratorUrl,
        instanceId: cloudLink.instanceId,
        token: cloudLink.token,
        defaultRequestTimeoutMs: 30_000,
      });
      const cloudBackend = new RestAgentBackend({ transport: cloudTransport });

      const cloudSessions = await cloudBackend.listSessions();
      expect(cloudSessions.some((session) => session.session_id === sessionId)).toBe(true);

      const cloudMessages = await cloudBackend.listMessages(sessionId);
      expect(cloudMessages.messages[0]?.message.content).toBe('local hello');

      const transferredLocalFile = await cloudTransport.request<{ content: string }>({
        method: 'GET',
        path: '/cloud-agent/workspace/files/local.txt',
        timeoutMs: 30_000,
      });
      expect(transferredLocalFile.data.content).toBe('local file\n');

      await cloudTransport.request({
        method: 'POST',
        path: '/cloud-agent/workspace/files',
        body: {
          path: 'from-cloud.txt',
          content: 'synced from cloud',
        },
        timeoutMs: 30_000,
      });

      await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.sync_down',
        actionOwner: 'application',
        inputs: {
          instance_id: cloudLink.instanceId,
          workspace_dir: workspaceDir,
        },
      });

      expect(fs.readFileSync(path.join(workspaceDir, 'from-cloud.txt'), 'utf8')).toBe(
        'synced from cloud',
      );

      await cloudBackend.appendMessage(sessionId, {
        role: 'assistant',
        content: 'remote hello',
      });

      await localBackend.executeAction({
        pluginId: 'cloud',
        actionId: 'cloud.close_session',
        actionOwner: 'application',
        inputs: {
          instance_id: cloudLink.instanceId,
          session_id: sessionId,
        },
      });

      const localMessages = await localBackend.listMessages(sessionId);
      expect(localMessages.messages.map((entry) => entry.message.content)).toContain('remote hello');
    },
    TEST_TIMEOUT_MS,
  );
});