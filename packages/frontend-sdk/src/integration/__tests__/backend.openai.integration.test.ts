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
import { startBackendServer, waitFor } from '../harness';

function findRepoRoot(fromDir: string): string {
  let current = fromDir;
  for (let i = 0; i < 10; i += 1) {
    if (fs.existsSync(path.join(current, 'core', 'python'))) {
      return current;
    }
    const next = path.dirname(current);
    if (next === current) break;
    current = next;
  }
  throw new Error(`Unable to find repo root from ${fromDir}`);
}

function loadEnvVarFromRoot(name: string): string | null {
  const existing = process.env[name];
  if (typeof existing === 'string' && existing.trim()) {
    return existing.trim();
  }

  const repoRoot = findRepoRoot(process.cwd());
  const envPath = path.join(repoRoot, '.env');
  if (!fs.existsSync(envPath)) {
    return null;
  }

  const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const match = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match || match[1] !== name) continue;
    let value = match[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (value) {
      process.env[name] = value;
      return value;
    }
  }

  return null;
}

function generateRedSquarePngBase64(): { filename: string; dataBase64: string } {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-sdk-openai-attachment-'));
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

const OPENAI_API_KEY = loadEnvVarFromRoot('OPENAI_API_KEY');
const OPENAI_BASE_URL = loadEnvVarFromRoot('OPENAI_BASE_URL');
const RUN = process.env.RUN_BACKEND_OPENAI_INTEGRATION === '1' && !!OPENAI_API_KEY;
const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + frontend SDK + OpenAI Responses attachments)', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  it('stores an attachment through the SDK action helper and sends it by asset_ref against the real API', async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const openaiResponsesPluginDir = path.join(repoRoot, 'plugins', 'openai_responses');
    const started = await startBackendServer({
      config: {
        plugin_cache_dir: '.plugin_cache',
        providers: {
          openai: {
            provider: 'openai_responses',
            model: process.env.OPENAI_RESPONSES_VISION_MODEL || 'gpt-5-mini',
            api_key: OPENAI_API_KEY,
            base_url: OPENAI_BASE_URL || 'https://api.openai.com/v1',
            timeout: 120,
            attachment_upload_mode: 'upload_before_send',
          },
        },
        plugins: [`path:${openaiResponsesPluginDir}`],
        agents: { default: { provider: 'openai' } },
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
      expect(imageAttachmentElement?.plugin).toBe('openai_responses');
      expect(imageAttachmentElement?.attachment_action_plugin).toBe('openai_responses_attachments');
      const attachmentPluginId = resolveAttachmentActionPluginId(imageAttachmentElement);
      expect(attachmentPluginId).toBe('openai_responses_attachments');

      const image = generateRedSquarePngBase64();
      const asset = await storeSessionAttachment({
        backend,
        sessionId,
        attachmentType: 'image',
        filename: image.filename,
        mimeType: 'image/png',
        dataBase64: image.dataBase64,
        clientAttachmentId: 'sdk-openai-draft-image',
        pluginId: attachmentPluginId ?? '',
      });

      await controller.appendMessage({
        role: 'user',
        content:
          'Reply with exactly SDK_ASSET_OK if the stored attachment is a solid red square image. Otherwise reply with exactly SDK_ASSET_FAIL.',
        multipartContent: [
          {
            type: 'image',
            content: {
              asset_ref: asset.asset_ref,
              filename: asset.filename,
              mime_type: asset.mime_type,
            },
            metadata: { source: 'sdk-openai-e2e' },
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
          lastAssistant.message.content.includes('SDK_ASSET_OK')
        );
      }, { timeoutMs: 180000, intervalMs: 250 });

      const listed = await backend.listMessages(sessionId);
      const userWithAttachment = listed.messages.find((message) =>
        Array.isArray((message.message as any).multipartContent) &&
        ((message.message as any).multipartContent[0]?.content?.asset_ref?.asset_id === asset.asset_ref.asset_id),
      );

      expect(userWithAttachment).toBeDefined();
      const lastAssistant = [...listed.messages].reverse().find((message) => message.message.role === 'assistant');
      expect(typeof lastAssistant?.message.content).toBe('string');
      expect(String(lastAssistant?.message.content)).toContain('SDK_ASSET_OK');
    } finally {
      controller.stopEventStreaming();
    }
  }, 300000);
});