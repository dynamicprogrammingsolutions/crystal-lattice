import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import { emitServerSettingsInvalidated } from '../serverSettings/serverSettingsInvalidation';
import { SessionsController } from './sessionsController';

describe('SessionsController', () => {
  it('reloads server-provided session presentation after server settings change', async () => {
    const backend = {
      listSessions: vi
        .fn()
        .mockResolvedValueOnce([
          {
            session_id: 's1',
            modified: 1,
            preview: 'preview',
            metadata: { status: 'done' },
            presentation: {
              title: 'Session',
              subtitle: null,
              meta: '2 messages',
            },
          },
        ])
        .mockResolvedValueOnce([
          {
            session_id: 's1',
            modified: 1,
            preview: 'preview',
            metadata: { status: 'done' },
            presentation: {
              title: 'Session',
              subtitle: null,
              meta: '2 messages · Status: Done',
            },
          },
        ]),
    } as unknown as AgentBackend;

    const controller = new SessionsController({ backend });
    await controller.load();
    expect(controller.getSnapshot().sessions[0].presentation?.meta).toBe(
      '2 messages',
    );

    emitServerSettingsInvalidated(backend, {
      reason: 'server_settings_updated',
    });

    await vi.waitFor(() => {
      expect(controller.getSnapshot().sessions[0].presentation?.meta).toBe(
        '2 messages · Status: Done',
      );
    });
    expect(backend.listSessions).toHaveBeenCalledTimes(2);

    controller.close();
    emitServerSettingsInvalidated(backend, {
      reason: 'server_settings_updated',
    });
    await Promise.resolve();
    expect(backend.listSessions).toHaveBeenCalledTimes(2);
  });
});