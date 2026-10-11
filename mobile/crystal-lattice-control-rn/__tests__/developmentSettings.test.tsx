import { act, renderHook, waitFor } from '@testing-library/react-native';
import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import {
  DEVELOPMENT_SETTINGS_STORAGE_KEY,
  loadDevelopmentSettings,
  withDevelopmentBridgeMode,
} from '../src/settings/developmentSettings';
import { useDevelopmentSettings } from '../src/settings/useDevelopmentSettings';
import { useSavedBridgeUrls } from '../src/connections/useSavedBridgeUrls';

function storage(initial: Record<string, string> = {}): KeyValueStore {
  const data = new Map(Object.entries(initial));
  return {
    get: jest.fn(async (key: string) => data.get(key) ?? null),
    set: jest.fn(async (key: string, value: string) => { data.set(key, value); }),
    delete: async (key: string) => { data.delete(key); },
  };
}

it.each(['not-json', '{}', '[]', '{"version":1,"bridgeTransportOverride":"invalid"}'])(
  'uses HTTP when preferences are absent or malformed: %s', async (raw) => {
    expect(await loadDevelopmentSettings(storage({ [DEVELOPMENT_SETTINGS_STORAGE_KEY]: raw })))
      .toEqual({ version: 1 });
  },
);

it('persists diagnostic selection and resets only transport, preserving other settings', async () => {
  const store = storage({
    [DEVELOPMENT_SETTINGS_STORAGE_KEY]: JSON.stringify({ version: 1, futureSetting: true }),
  });
  const first = renderHook(() => useDevelopmentSettings(store));
  await waitFor(() => expect(first.result.current.hydrated).toBe(true));
  await act(async () => { await first.result.current.setBridgeMode('hybrid'); });
  expect(first.result.current.mode).toBe('hybrid');
  first.unmount();
  const reopened = renderHook(() => useDevelopmentSettings(store));
  await waitFor(() => expect(reopened.result.current.mode).toBe('hybrid'));
  await act(async () => { await reopened.result.current.setBridgeMode('http'); });
  expect(reopened.result.current.settings).toEqual({ version: 1, futureSetting: true });
  expect(JSON.parse((await store.get(DEVELOPMENT_SETTINGS_STORAGE_KEY))!))
    .toEqual({ version: 1, futureSetting: true });
});

it('serializes successive preference updates against the most recent persisted value', async () => {
  const store = storage();
  const hook = renderHook(() => useDevelopmentSettings(store));
  await waitFor(() => expect(hook.result.current.hydrated).toBe(true));
  await act(async () => {
    await Promise.all([
      hook.result.current.setBridgeMode('websocket'),
      hook.result.current.setBridgeMode('hybrid'),
    ]);
  });
  expect(hook.result.current.mode).toBe('hybrid');
  expect(withDevelopmentBridgeMode({ version: 1, other: 1 }, 'http'))
    .toEqual({ version: 1, other: 1 });
});

it('waits for saved-endpoint hydration and upserts/removes through the real hook', async () => {
  let resolveLoad!: (raw: string | null) => void;
  const store = storage();
  jest.mocked(store.get).mockImplementationOnce(
    () => new Promise((resolve) => { resolveLoad = resolve; }),
  );
  const hook = renderHook(() => useSavedBridgeUrls(store));
  expect(hook.result.current.hydrated).toBe(false);
  expect(store.set).not.toHaveBeenCalled();
  await act(async () => {
    resolveLoad(JSON.stringify([{ url: 'wss://one/ws', label: 'Office', lastUsedAt: 1 }]));
  });
  await act(async () => {
    await Promise.all([
      hook.result.current.remember('wss://one/ws'),
      hook.result.current.remember('ws://two/ws'),
    ]);
  });
  expect(hook.result.current.bridges).toHaveLength(2);
  expect(hook.result.current.bridges.find((entry) => entry.url === 'wss://one/ws'))
    .toMatchObject({ label: 'Office' });
  await act(async () => { await hook.result.current.remove('ws://two/ws'); });
  expect(hook.result.current.bridges.map((entry) => entry.url)).toEqual(['wss://one/ws']);
});