import React from 'react';
import { Text } from 'react-native';
import { fireEvent, render, waitFor } from '@testing-library/react-native';

import GlobalSettingsModal from '../src/components/GlobalSettingsModal';
import {
  HomeWorkspaceProvider,
  useHomeWorkspace,
} from '../src/HomeWorkspaceContext';
import {
  DEFAULT_TIME_TRACKING_PLUGIN_ID,
  MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY,
} from '../src/homeWorkspaceState';

function createMemoryStore() {
  const data = new Map<string, string>();
  return {
    get: async (key: string) => data.get(key) ?? null,
    set: async (key: string, value: string) => {
      data.set(key, value);
    },
    delete: async (key: string) => {
      data.delete(key);
    },
    raw: () => data,
  };
}

function PreferenceProbe() {
  const workspace = useHomeWorkspace();
  return (
    <Text testID="workspace-probe">
      {JSON.stringify({
        hydrated: workspace.hydrated,
        timeTrackingEnabled: workspace.timeTrackingEnabled,
        timeTrackingPluginId: workspace.timeTrackingPluginId,
      })}
    </Text>
  );
}

function Host({ store }: { store: ReturnType<typeof createMemoryStore> }) {
  return (
    <HomeWorkspaceProvider store={store}>
      <GlobalSettingsModal visible onRequestClose={() => {}} />
      <PreferenceProbe />
    </HomeWorkspaceProvider>
  );
}

function readPreferences(store: ReturnType<typeof createMemoryStore>) {
  const raw = store.raw().get(MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

async function waitForHydration(store: ReturnType<typeof createMemoryStore>) {
  await waitFor(async () => {
    const persisted = await readPreferences(store);
    // The provider persists once hydrated; the initial write marks it.
    expect(persisted).not.toBeNull();
  });
}

describe('time tracking settings', () => {
  it('renders the opt-in toggle (default off) and the telemetry plugin field', () => {
    const store = createMemoryStore();
    const { getByTestId } = render(<Host store={store} />);

    const toggle = getByTestId('global-settings-time-tracking-toggle');
    expect(toggle.props.value).toBe(false);
    const pluginInput = getByTestId('global-settings-telemetry-plugin-input');
    expect(pluginInput.props.value).toBe(DEFAULT_TIME_TRACKING_PLUGIN_ID);
  });

  it('persists the opt-in toggle through the preferences store', async () => {
    const store = createMemoryStore();
    const { getByTestId } = render(<Host store={store} />);
    await waitForHydration(store);

    fireEvent(getByTestId('global-settings-time-tracking-toggle'), 'valueChange', true);

    await waitFor(() => {
      expect(readPreferences(store)?.timeTrackingEnabled).toBe(true);
    });
  });

  it('persists the telemetry plugin id and falls back to the default when emptied', async () => {
    const store = createMemoryStore();
    const { getByTestId } = render(<Host store={store} />);
    await waitForHydration(store);

    const input = getByTestId('global-settings-telemetry-plugin-input');
    fireEvent.changeText(input, 'my_custom_plugin');
    await waitFor(() => {
      expect(readPreferences(store)?.timeTrackingPluginId).toBe('my_custom_plugin');
    });

    fireEvent.changeText(input, '   ');
    await waitFor(() => {
      expect(readPreferences(store)?.timeTrackingPluginId).toBe(
        DEFAULT_TIME_TRACKING_PLUGIN_ID,
      );
    });
  });

  it('hydrates persisted time tracking preferences', async () => {
    const store = createMemoryStore();
    await store.set(
      MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY,
      JSON.stringify({
        timeTrackingEnabled: true,
        timeTrackingPluginId: 'persisted_plugin',
      }),
    );

    const { getByTestId, findByTestId } = render(<Host store={store} />);
    const probe = await findByTestId('workspace-probe');
    expect(JSON.parse(probe.props.children)).toEqual({
      hydrated: true,
      timeTrackingEnabled: true,
      timeTrackingPluginId: 'persisted_plugin',
    });
    expect(getByTestId('global-settings-time-tracking-toggle').props.value).toBe(true);
  });
});