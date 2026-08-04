import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Text } from 'react-native';
import { render, waitFor } from '@testing-library/react-native';

import {
  PinnedActionsProvider,
  usePersistentPinnedActionsFromContext,
} from '../src/PinnedActionsContext';

function Probe({ initialPinned }: { initialPinned: string[] }) {
  const { loaded, pinned } = usePersistentPinnedActionsFromContext(
    'rich-session-actions',
    initialPinned,
  );
  return (
    <Text testID="pinned-actions-probe">
      {loaded ? JSON.stringify(pinned) : 'loading'}
    </Text>
  );
}

function renderProbe(initialPinned: string[]) {
  return render(
    <PinnedActionsProvider>
      <Probe initialPinned={initialPinned} />
    </PinnedActionsProvider>,
  );
}

beforeEach(async () => {
  await (AsyncStorage as any).clear();
});

test('adopts rich defaults that arrive after absent storage resolves', async () => {
  const rendered = renderProbe(['agentSwitch']);
  await waitFor(() => {
    expect(rendered.getByTestId('pinned-actions-probe').props.children).toBe(
      '["agentSwitch"]',
    );
  });

  rendered.rerender(
    <PinnedActionsProvider>
      <Probe
        initialPinned={[
          'agentSwitch',
          'toggle_session_pinned',
          'toggle_session_archived',
        ]}
      />
    </PinnedActionsProvider>,
  );

  await waitFor(() => {
    expect(rendered.getByTestId('pinned-actions-probe').props.children).toBe(
      '["agentSwitch","toggle_session_pinned","toggle_session_archived"]',
    );
  });
});

test('preserves a stored empty preference when rich defaults change', async () => {
  await (AsyncStorage as any).setItem('rich-session-actions', '[]');
  const rendered = renderProbe(['toggle_session_pinned']);
  await waitFor(() => {
    expect(rendered.getByTestId('pinned-actions-probe').props.children).toBe('[]');
  });

  rendered.rerender(
    <PinnedActionsProvider>
      <Probe initialPinned={['toggle_session_pinned', 'toggle_session_archived']} />
    </PinnedActionsProvider>,
  );
  await waitFor(() => {
    expect(rendered.getByTestId('pinned-actions-probe').props.children).toBe('[]');
  });
});