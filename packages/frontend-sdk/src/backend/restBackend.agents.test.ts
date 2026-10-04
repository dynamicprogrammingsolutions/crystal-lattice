import { describe, expect, it, vi } from 'vitest';

import type { Transport } from '../transport/transport';
import { RestAgentBackend } from './restBackend';

describe('RestAgentBackend agents', () => {
  it('preserves the legacy string list and parses ordered descriptors', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          agents: ['codex', 'claude'],
          agent_descriptors: [
            {
              id: 'claude',
              title: 'Claude',
              description: 'Claude-oriented tools.',
              order: 20,
            },
            {
              id: 'codex',
              title: 'Codex',
              description: 'Codex-oriented tools.',
              order: 10,
            },
          ],
        },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.listAgents()).resolves.toEqual(['codex', 'claude']);
    await expect(backend.listAgentDescriptors()).resolves.toEqual([
      {
        id: 'claude',
        title: 'Claude',
        description: 'Claude-oriented tools.',
        order: 20,
      },
      {
        id: 'codex',
        title: 'Codex',
        description: 'Codex-oriented tools.',
        order: 10,
      },
    ]);
  });

  it('normalizes descriptor text and rejects invalid entries', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          agent_descriptors: [
            { id: ' codex ', title: ' ', description: ' tools ', order: 5 },
            { id: '', title: 'missing' },
            null,
          ],
        },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.listAgentDescriptors()).resolves.toEqual([
      {
        id: 'codex',
        title: 'codex',
        description: 'tools',
        order: 5,
      },
    ]);
  });

  it('lists only normalized safe agent plugin metadata', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          plugins: [
            {
              id: ' apply_patch ',
              kind: ' tools ',
              name: ' apply_patch ',
              class_path: ' codex_tools.ApplyPatchTool ',
              class_name: ' ApplyPatchTool ',
              enabled: true,
              active: true,
              source: 'agent',
              api_key: 'must-not-cross-the-sdk',
            },
            { id: '', kind: 'tools', enabled: true, active: true },
          ],
        },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.listAgentPlugins('codex/openai')).resolves.toEqual([
      {
        id: 'apply_patch',
        kind: 'tools',
        name: 'apply_patch',
        class_path: 'codex_tools.ApplyPatchTool',
        class_name: 'ApplyPatchTool',
        enabled: true,
        active: true,
        source: 'agent',
      },
    ]);
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path: '/agents/codex%2Fopenai/plugins',
    });
  });
});