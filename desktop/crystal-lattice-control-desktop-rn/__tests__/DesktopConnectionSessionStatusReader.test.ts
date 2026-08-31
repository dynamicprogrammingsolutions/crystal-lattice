import type {
  AgentBackend,
  ConnectionRecord,
  SessionRequestStatusSnapshot,
} from '@crystal-lattice/frontend-sdk';

import { DesktopConnectionSessionStatusReader } from '../src/status/DesktopConnectionSessionStatusReader';

const snapshot: SessionRequestStatusSnapshot = {
  version: 1,
  authority: 'derived_transient',
  statuses: [],
  missing_session_ids: [],
};

describe('DesktopConnectionSessionStatusReader', () => {
  it('uses an already-open backend without constructing another connection', async () => {
    const getSessionRequestStatuses = jest.fn(async () => snapshot);
    const backend = { getSessionRequestStatuses } as unknown as AgentBackend;
    const reader = new DesktopConnectionSessionStatusReader(() => backend);
    const record = {
      id: 'connection',
      name: 'Local',
      kind: 'manual',
      host: '127.0.0.1',
      port: 9000,
    } as ConnectionRecord;

    await expect(
      reader.getSessionRequestStatuses(record, ['session']),
    ).resolves.toEqual({ status: 'ok', snapshot });
    expect(getSessionRequestStatuses).toHaveBeenCalledWith(['session'], {
      signal: undefined,
    });
  });

  it('degrades unsupported closed connection kinds without opening them', async () => {
    const reader = new DesktopConnectionSessionStatusReader(() => null);
    const record = {
      id: 'cloud',
      name: 'Cloud',
      kind: 'cloud',
    } as ConnectionRecord;
    await expect(
      reader.getSessionRequestStatuses(record, ['session']),
    ).resolves.toEqual({ status: 'unsupported' });
  });
});
