import { afterAll, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import {
  downloadSessionAttachment,
  selectAttachmentPreviewUrl,
  storeSessionAttachment,
} from '../../index';
import { startBackendServer, waitForAsync } from '../harness';

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

function generateSourceImageBase64(): { filename: string; dataBase64: string } {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-sdk-openrouter-image-'));
  const imagePath = path.join(tmpDir, 'sdk-source-image.png');
  try {
    execFileSync('magick', ['-size', '128x128', 'xc:white', '-fill', '#1e6eea', '-draw', 'circle 64,64 64,18', imagePath], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (error: any) {
    const detail = typeof error?.stderr === 'string' ? error.stderr : String(error?.message || error);
    throw new Error(`failed to generate SDK source image fixture with ImageMagick: ${detail}`);
  }

  const dataBase64 = fs.readFileSync(imagePath).toString('base64');
  return { filename: 'sdk-source-image.png', dataBase64 };
}

async function waitForAssistantImage(
  backend: RestAgentBackend,
  sessionId: string,
): Promise<{
  listed: Awaited<ReturnType<RestAgentBackend['listMessages']>>;
  assistant: any;
}> {
  await waitForAsync(async () => {
    const listed = await backend.listMessages(sessionId);
    return (
      listed.activeRequestId == null &&
      listed.messages.some(
        (message) =>
          message.message.role === 'assistant' &&
          Array.isArray((message.message as any).multipartContent),
      )
    );
  }, { timeoutMs: 180000, intervalMs: 250 });

  const listed = await backend.listMessages(sessionId);
  const assistant = [...listed.messages].reverse().find(
    (message) =>
      message.message.role === 'assistant' &&
      Array.isArray((message.message as any).multipartContent),
  );
  if (!assistant) {
    throw new Error('assistant image response not found after request completion');
  }
  return { listed, assistant };
}

async function getImageAttachmentPluginId(
  backend: RestAgentBackend,
  sessionId: string,
): Promise<string> {
  const elements = await backend.getSessionUiSchema(sessionId);
  const imageAttachmentElement = elements.find(
    (element: any) =>
      element &&
      element.ui_type === 'composer_attachment' &&
      element.attachment_type === 'image',
  ) as any;

  if (!imageAttachmentElement || typeof imageAttachmentElement.plugin !== 'string') {
    throw new Error('image composer attachment plugin was not exposed in session UI schema');
  }
  return imageAttachmentElement.plugin;
}

const OPENROUTER_API_KEY = loadEnvVarFromRoot('OPENROUTER_API_KEY');
const OPENROUTER_BASE_URL = loadEnvVarFromRoot('OPENROUTER_BASE_URL');
const OPENROUTER_IMAGE_MODEL =
  loadEnvVarFromRoot('OPENROUTER_IMAGE_GENERATION_E2E_MODEL') ||
  'google/gemini-2.5-flash-image';
const RUN = process.env.RUN_BACKEND_OPENROUTER_INTEGRATION === '1' && !!OPENROUTER_API_KEY;
const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + frontend SDK + OpenRouter image generation)', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  it('covers simple generation, source-image generation, and result download against the real provider', async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const openrouterPluginDir = path.join(repoRoot, 'plugins', 'openrouter');
    const started = await startBackendServer({
      config: {
        plugin_cache_dir: '.plugin_cache',
        providers: {
          openrouter_image: {
            provider: 'openrouter_image_generation',
            model: OPENROUTER_IMAGE_MODEL,
            api_key: OPENROUTER_API_KEY,
            base_url: OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
            timeout: 180,
            aspect_ratio: '1:1',
          },
        },
        plugins: [`path:${openrouterPluginDir}`],
        agents: { default: { provider: 'openrouter_image' } },
      },
    });
    stopServer = started.stop;

    const transport = new FetchTransport({ baseUrl: started.baseUrl });
    const backend = new RestAgentBackend({ transport });

    try {
      const simpleCreated = await backend.createSession({ agentId: 'default' });
      const simpleSessionId = simpleCreated.session.session_id;

      await backend.appendMessage(simpleSessionId, {
        role: 'user',
        content: 'Generate a simple flat orange square icon on a plain background.',
      });
      await backend.send(simpleSessionId, { configOverrides: {} });

      const simpleResult = await waitForAssistantImage(backend, simpleSessionId);
      const simplePart = (simpleResult.assistant.message as any)?.multipartContent?.[0] ?? {};
      expect(selectAttachmentPreviewUrl(simplePart.content)).toMatch(/^data:image\//);

      const sourceCreated = await backend.createSession({ agentId: 'default' });
      const sourceSessionId = sourceCreated.session.session_id;
      const sourceImage = generateSourceImageBase64();
      const imageAttachmentPluginId = await getImageAttachmentPluginId(backend, sourceSessionId);
      const uploadedAsset = await storeSessionAttachment({
        backend,
        sessionId: sourceSessionId,
        attachmentType: 'image',
        filename: sourceImage.filename,
        mimeType: 'image/png',
        dataBase64: sourceImage.dataBase64,
        pluginId: imageAttachmentPluginId,
      });

      await backend.appendMessage(sourceSessionId, {
        role: 'user',
        content:
          'Use the attached source image as inspiration and generate a polished blue circular badge variation on a plain background.',
        multipartContent: [
          {
            type: 'image',
            content: {
              asset_ref: uploadedAsset.asset_ref,
              filename: uploadedAsset.filename,
              mime_type: uploadedAsset.mime_type,
            },
            metadata: {},
          },
        ],
      });
      await backend.send(sourceSessionId, { configOverrides: {} });

      const sourceResult = await waitForAssistantImage(backend, sourceSessionId);
      const generatedPart = (sourceResult.assistant.message as any)?.multipartContent?.[0] ?? {};
      expect(selectAttachmentPreviewUrl(generatedPart.content)).toMatch(/^data:image\//);
      expect(generatedPart.metadata?.download_plugin_id).toBe(imageAttachmentPluginId);

      const generatedAssetId = generatedPart.content?.asset_ref?.asset_id;
      expect(typeof generatedAssetId).toBe('string');
      const downloaded = await downloadSessionAttachment({
        backend,
        sessionId: sourceSessionId,
        assetId: generatedAssetId,
        pluginId: imageAttachmentPluginId,
      });
      expect(downloaded.attachment_asset.asset_ref.asset_id).toBe(generatedAssetId);
      expect(downloaded.data_base64.length).toBeGreaterThan(1000);
    } finally {
      await started.stop();
      stopServer = null;
    }
  }, 420000);
});