import React from 'react';
import { Pressable, Text, View } from 'react-native';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

import { useSynchronizedPersistentPinnedActions } from '../src/chat/useSynchronizedPersistentPinnedActions';

const INITIAL_PINNED = ['reload'];

function PinConsumer({
  id,
  storageKey,
  store,
}: {
  id: string;
  storageKey: string;
  store: KeyValueStore;
}): React.JSX.Element {
  const { loaded, pinned, setPinned } =
    useSynchronizedPersistentPinnedActions<string>({
      store,
      key: storageKey,
      initialPinned: INITIAL_PINNED,
    });

  return (
    <View>
      <Text testID={`pins-${id}`}>
        {loaded ? 'loaded' : 'loading'}:{pinned.join(',')}
      </Text>
      <Pressable
        testID={`pin-settings-${id}`}
        onPress={() =>
          setPinned(current =>
            current.includes('settings')
              ? current.filter(key => key !== 'settings')
              : [...current, 'settings'],
          )
        }
      />
    </View>
  );
}

function createStore(
  get: KeyValueStore['get'] = async () => null,
): KeyValueStore & { set: jest.Mock } {
  return {
    get,
    set: jest.fn(async () => {}),
    delete: jest.fn(async () => {}),
  };
}

describe('synchronized desktop pinned actions', () => {
  it('updates existing consumers of the same connection key immediately', async () => {
    const store = createStore();
    render(
      <>
        <PinConsumer
          id="first"
          storageKey="session-actions:one"
          store={store}
        />
        <PinConsumer
          id="second"
          storageKey="session-actions:one"
          store={store}
        />
        <PinConsumer
          id="other"
          storageKey="session-actions:two"
          store={store}
        />
      </>,
    );

    await waitFor(() =>
      expect(screen.getByTestId('pins-first').props.children.join('')).toBe(
        'loaded:reload',
      ),
    );
    fireEvent.press(screen.getByTestId('pin-settings-first'));

    expect(screen.getByTestId('pins-first').props.children.join('')).toBe(
      'loaded:reload,settings',
    );
    expect(screen.getByTestId('pins-second').props.children.join('')).toBe(
      'loaded:reload,settings',
    );
    expect(screen.getByTestId('pins-other').props.children.join('')).toBe(
      'loaded:reload',
    );
    expect(store.set).toHaveBeenCalledTimes(1);
    expect(store.set).toHaveBeenCalledWith(
      'session-actions:one',
      JSON.stringify(['reload', 'settings']),
    );

    fireEvent.press(screen.getByTestId('pin-settings-second'));
    expect(screen.getByTestId('pins-first').props.children.join('')).toBe(
      'loaded:reload',
    );
    expect(screen.getByTestId('pins-second').props.children.join('')).toBe(
      'loaded:reload',
    );
    expect(store.set).toHaveBeenCalledTimes(2);
    expect(store.set).toHaveBeenLastCalledWith(
      'session-actions:one',
      JSON.stringify(['reload']),
    );
  });

  it('does not let an older in-flight storage read replace a live tab update', async () => {
    let resolveStored!: (value: string | null) => void;
    const stored = new Promise<string | null>(resolve => {
      resolveStored = resolve;
    });
    const store = createStore(async () => stored);
    render(
      <>
        <PinConsumer
          id="first"
          storageKey="session-actions:one"
          store={store}
        />
        <PinConsumer
          id="second"
          storageKey="session-actions:one"
          store={store}
        />
      </>,
    );

    fireEvent.press(screen.getByTestId('pin-settings-first'));
    expect(screen.getByTestId('pins-second').props.children.join('')).toBe(
      'loaded:reload,settings',
    );

    await act(async () => {
      resolveStored(JSON.stringify(['reload']));
      await stored;
      await Promise.resolve();
    });
    expect(screen.getByTestId('pins-first').props.children.join('')).toBe(
      'loaded:reload,settings',
    );
    expect(screen.getByTestId('pins-second').props.children.join('')).toBe(
      'loaded:reload,settings',
    );
  });
});
