import { afterAll, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import { ChatController } from '../../chat/chatController';
import {
  resolveAttachmentActionPluginId,
  storeSessionAttachment,
} from '../../plugins/attachmentActions';
import {
  findRepoRoot,
  loadEnvVarFromRoot,
  startBackendServer,
  waitFor,
} from '../harness';

function generateRedSquarePngBase64(): { filename: string; dataBase64: string } {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-sdk-openrouter-attachment-'));
  const imagePath = path.join(tmpDir, 'sdk-red-square.png');
  try {
    execFileSync('magick', ['-size', '96x96', 'xc:red', imagePath], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (error: any) {
    const detail = typeof error?.stderr === 'string' ? error.stderr : String(error?.message || error);
    throw new Error(`failed to generate SDK image fixture with ImageMagick: ${detail}`);
  }

  const dataBase64 = fs.readFileSync(imagePath).toString('base64');
  return { filename: 'sdk-red-square.png', dataBase64 };
}

const OPENROUTER_API_KEY = loadEnvVarFromRoot('OPENROUTER_API_KEY');
const OPENROUTER_BASE_URL = loadEnvVarFromRoot('OPENROUTER_BASE_URL');
const OPENROUTER_VISION_MODEL =
  loadEnvVarFromRoot('OPENROUTER_VISION_MODEL') || 'google/gemini-2.5-flash-lite';
const RUN = !!OPENROUTER_API_KEY;
const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + frontend SDK + OpenRouter chat attachments)', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  it('stores an attachment through the SDK action helper and sends it by asset_ref against the real API', async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const openrouterPluginDir = path.join(repoRoot, 'plugins', 'openrouter');
    const started = await startBackendServer({
      config: {
        plugin_cache_dir: '.plugin_cache',
        providers: {
          openrouter: {
            provider: 'openrouter',
            model: OPENROUTER_VISION_MODEL,
            api_key: OPENROUTER_API_KEY,
            base_url: OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
            timeout: 120,
          },
        },
        plugins: [`path:${openrouterPluginDir}`],
        agents: { default: { provider: 'openrouter' } },
      },
      startupTimeoutMs: 120000,
    });
    stopServer = started.stop;

    const transport = new FetchTransport({ baseUrl: started.baseUrl });
    const backend = new RestAgentBackend({ transport });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;

    const controller = new ChatController({ backend, sessionId });
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
    controller.startEventStreaming({ initialSinceId: controller.getSnapshot().eventsCursorId });

    try {
      const sessionUiElements = await backend.getSessionUiSchema(sessionId);
      const imageAttachmentElement = sessionUiElements.find(
        (element: any) =>
          element &&
          element.ui_type === 'composer_attachment' &&
          element.attachment_type === 'image',
      ) as any;

      expect(imageAttachmentElement?.plugin).toBe('openrouter_attachments');
      expect(imageAttachmentElement?.attachment_action_plugin).toBe('openrouter_attachments');
      const attachmentPluginId = resolveAttachmentActionPluginId(imageAttachmentElement);
      expect(attachmentPluginId).toBe('openrouter_attachments');

      const image = generateRedSquarePngBase64();
      const asset = await storeSessionAttachment({
        backend,
        sessionId,
        attachmentType: 'image',
        filename: image.filename,
        mimeType: 'image/png',
        dataBase64: image.dataBase64,
        clientAttachmentId: 'sdk-openrouter-draft-image',
        pluginId: attachmentPluginId ?? '',
      });

      await controller.appendMessage({
        role: 'user',
        content:
          'Reply with exactly SDK_OPENROUTER_ASSET_OK if the stored attachment is a solid red square image. Otherwise reply with exactly SDK_OPENROUTER_ASSET_FAIL.',
        multipartContent: [
          {
            type: 'image',
            content: {
              asset_ref: asset.asset_ref,
              filename: asset.filename,
              mime_type: asset.mime_type,
            },
            metadata: { download_plugin_id: attachmentPluginId },
          },
        ],
      });

      await controller.send({ configOverrides: {} });

      await waitFor(() => {
        const snapshot = controller.getSnapshot();
        const lastAssistant = [...snapshot.messages].reverse().find((message) => message.message.role === 'assistant');
        return (
          snapshot.dirty === false &&
          snapshot.activeRequestId == null &&
          typeof lastAssistant?.message.content === 'string' &&
          lastAssistant.message.content.includes('SDK_OPENROUTER_ASSET_OK')
        );
      }, { timeoutMs: 180000, intervalMs: 250 });

      const listed = await backend.listMessages(sessionId);
      const userWithAttachment = listed.messages.find((message) =>
        Array.isArray((message.message as any).multipartContent) &&
        ((message.message as any).multipartContent[0]?.content?.asset_ref?.asset_id === asset.asset_ref.asset_id),
      );

      expect(userWithAttachment).toBeDefined();
      expect((userWithAttachment?.message as any)?.multipartContent?.[0]?.metadata?.download_plugin_id).toBe(
        'openrouter_attachments',
      );

      const lastAssistant = [...listed.messages].reverse().find((message) => message.message.role === 'assistant');
      expect(typeof lastAssistant?.message.content).toBe('string');
      expect(String(lastAssistant?.message.content)).toContain('SDK_OPENROUTER_ASSET_OK');
    } finally {
      controller.stopEventStreaming();
      await started.stop();
      stopServer = null;
    }
  }, 300000);
});