import React from 'react';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react-native';
import { Alert } from 'react-native';
import {
  FetchTransport,
  RestAgentBackend,
} from '@crystal-lattice/frontend-sdk';
import {
  startAcknowledgementProxy,
  startChatOperationsBackend,
} from '../../../test/fixture/chat-operations/backend';
import { ChatPaneTabStack } from '../src/tabs/ChatPaneTabStack';

jest.setTimeout(60_000);

let started: Awaited<ReturnType<typeof startChatOperationsBackend>>;
let proxy: Awaited<ReturnType<typeof startAcknowledgementProxy>>;
let backend: RestAgentBackend;
let rendered: ReturnType<typeof render> | null = null;
const requests: { event: string; method: string; path: string }[] = [];

beforeAll(async () => {
  started = await startChatOperationsBackend({
    messageCount: 8,
    firstMessageParts: [
      { type: 'text', content: 'Preserved part', metadata: { fixture: true } },
    ],
  });
  proxy = await startAcknowledgementProxy(started.server);
  backend = new RestAgentBackend({
    transport: new FetchTransport({
      baseUrl: proxy.baseUrl,
      debug: true,
      logger: (event, meta) =>
        requests.push({ event, method: meta?.method, path: meta?.path }),
    }),
  });
});
afterEach(async () => {
  rendered?.unmount();
  rendered = null;
  proxy?.setRule('none');
});
afterAll(async () => {
  await proxy?.stop();
  await started?.server.stop();
});

async function openChat() {
  const sessionId = started.sessions[0];
  rendered = render(
    <ChatPaneTabStack
      tabs={[
        {
          tabId: `local:${sessionId}`,
          connectionId: 'local',
          sessionId,
          title: 'Operations',
        },
      ]}
      activeTabId={`local:${sessionId}`}
      styleVariant="toolbarTabs"
      connectionNameById={{ local: 'Local' }}
      getBackend={() => backend}
      sessionsCache={{}}
      messagesCache={{}}
      onUpdateCache={() => {}}
      onOpenSessionTab={() => {}}
    />,
  );
  await screen.findByTestId('transcript-message-0');
  return sessionId;
}

test('modifies the selected message through the composer and restores its ordinary draft', async () => {
  const sessionId = await openChat();
  fireEvent.changeText(
    screen.getByTestId('message-composer-input'),
    'ordinary desktop draft',
  );
  fireEvent.press(
    within(screen.getByTestId('transcript-message-0')).getByTestId(
      'action-menu-item-modify',
    ),
  );
  expect(screen.getByTestId('composer-edit-label').props.children).toBe(
    'Editing message [0]',
  );
  expect(screen.getByLabelText('Save edit')).toBeTruthy();
  expect(
    screen.getByTestId('action-menu-item-append').props.accessibilityState
      .disabled,
  ).toBe(true);
  expect(
    screen.getByTestId('action-menu-item-resend').props.accessibilityState
      .disabled,
  ).toBe(true);
  expect(
    screen.getByTestId('action-menu-item-settings').props.accessibilityState
      .disabled,
  ).not.toBe(true);
  expect(screen.getByTestId('message-composer-input').props.value).toContain(
    'Message 0',
  );
  fireEvent.press(screen.getByTestId('composer-cancel-edit'));
  expect(screen.queryByTestId('composer-edit-context')).toBeNull();
  expect(screen.getByTestId('message-composer-input').props.value).toBe(
    'ordinary desktop draft',
  );
  fireEvent.press(
    within(screen.getByTestId('transcript-message-0')).getByTestId(
      'action-menu-item-modify',
    ),
  );
  fireEvent.changeText(
    screen.getByTestId('message-composer-input'),
    'modified desktop message',
  );
  proxy.setRule('reject-edit-before', 1);
  fireEvent.press(screen.getByTestId('composer-send'));
  await waitFor(() =>
    expect(proxy.receipts.some(entry => entry.stage === 'rejected-edit')).toBe(
      true,
    ),
  );
  await waitFor(() =>
    expect(screen.queryByTestId('composer-send-progress')).toBeNull(),
  );
  expect(screen.getByTestId('composer-edit-context')).toBeTruthy();
  expect(screen.getByTestId('message-composer-input').props.value).toBe(
    'modified desktop message',
  );
  expect(
    (await backend.listMessages(sessionId, {})).messages[0].message.content,
  ).toContain('Message 0');
  proxy.setRule('delay-edit');
  fireEvent.press(screen.getByTestId('composer-send'));
  await screen.findByTestId('composer-send-progress');
  expect(screen.getByTestId('chat-activity-label').props.children).toContain(
    'Saving message [0]',
  );
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 6000));
  });
  try {
    await waitFor(
      () => expect(screen.queryByTestId('composer-edit-context')).toBeNull(),
      { timeout: 15_000 },
    );
  } catch {
    throw new Error(
      `Edit did not finish. HTTP stages: ${JSON.stringify(
        proxy.receipts.slice(-20),
      )}; adapter: ${JSON.stringify(requests.slice(-12))}`,
    );
  }
  expect(screen.getByTestId('message-composer-input').props.value).toBe(
    'ordinary desktop draft',
  );
  const result = await backend.listMessages(sessionId, {});
  expect(result.messages[0].message.content).toBe('modified desktop message');
  expect(result.messages[0].message.role).toBe('user');
  expect(result.messages[0].message.metadata?.fixture).toBe(0);
  expect(result.messages[0].message.multipartContent).toEqual([
    { type: 'text', content: 'Preserved part', metadata: { fixture: true } },
  ]);
});

test('retries a lost send acknowledgement with the original payload and key', async () => {
  const sessionId = await openChat();
  const alert = jest.spyOn(Alert, 'alert');
  proxy.setRule('drop-send-after');
  fireEvent.changeText(
    screen.getByTestId('message-composer-input'),
    'desktop uncertain send',
  );
  fireEvent.press(screen.getByTestId('composer-send'));
  await screen.findByTestId('chat-send-recovery', {}, { timeout: 10_000 });
  expect(alert).not.toHaveBeenCalled();
  await waitFor(
    async () => {
      const status = await backend.getSessionRequestStatuses([sessionId]);
      expect(status.statuses[0].state).not.toBe('running');
    },
    { timeout: 15_000 },
  );
  proxy.setRule('none');
  await act(async () => {
    fireEvent.press(screen.getByTestId('chat-send-recovery-resend'));
    await new Promise(resolve => setTimeout(resolve, 250));
  });
  try {
    await waitFor(
      () => {
        expect(screen.queryByTestId('chat-send-recovery')).toBeNull();
        expect(screen.queryByTestId('composer-send-progress')).toBeNull();
      },
      { timeout: 10_000 },
    );
  } catch {
    throw new Error(
      `Retry did not settle. Activity: ${
        screen.queryByTestId('chat-activity-label')?.props.children
      }; status: ${JSON.stringify(
        await backend.getSessionRequestStatuses([sessionId]),
      )}; HTTP: ${JSON.stringify(
        proxy.receipts.filter(entry => entry.path.endsWith('/send_message')),
      )}; adapter: ${JSON.stringify(
        requests.filter(entry => entry.path?.endsWith('/send_message')),
      )}`,
    );
  }
  const result = await backend.listMessages(sessionId, {});
  expect(
    result.messages.filter(
      entry => entry.message.content === 'desktop uncertain send',
    ),
  ).toHaveLength(1);
  expect(screen.getByTestId('message-composer-input').props.value).toBe('');
  expect(screen.queryByTestId('composer-send-progress')).toBeNull();
  alert.mockRestore();
});

test('cancels local recovery while preserving the draft', async () => {
  await openChat();
  proxy.setRule('drop-send-before');
  fireEvent.changeText(
    screen.getByTestId('message-composer-input'),
    'desktop cancel draft',
  );
  fireEvent.press(screen.getByTestId('composer-send'));
  await screen.findByTestId('chat-send-recovery');
  fireEvent.press(screen.getByTestId('chat-send-recovery-cancel'));
  expect(screen.queryByTestId('chat-send-recovery')).toBeNull();
  expect(screen.getByTestId('message-composer-input').props.value).toBe(
    'desktop cancel draft',
  );
});

test('keeps another discovered action usable while a plugin action is running', async () => {
  await openChat();
  const slow = await screen.findByTestId('action-menu-item-slow');
  fireEvent.press(slow);
  await screen.findByTestId('chat-activity-progress');
  fireEvent.press(screen.getByTestId('action-menu-item-second'));
  await screen.findByText('second finished');
  expect(screen.getByTestId('chat-activity-label').props.children).toContain(
    'Slow action',
  );
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 10_000));
  });
  await waitFor(() =>
    expect(screen.queryByTestId('chat-activity-progress')).toBeNull(),
  );
});
