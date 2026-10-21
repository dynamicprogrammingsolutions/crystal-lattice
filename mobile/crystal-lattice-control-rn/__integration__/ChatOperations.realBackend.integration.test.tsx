import React from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react-native";
import { Alert, AppState } from "react-native";
import {
  FetchTransport,
  RestAgentBackend,
} from "@crystal-lattice/frontend-sdk";
import { ChatWorkspaceProvider } from "@crystal-lattice/frontend-sdk-react";
import {
  startAcknowledgementProxy,
  startChatOperationsBackend,
} from "../../../test/fixture/chat-operations/backend";
import SessionChatScreen from "../src/SessionChatScreen";
import { ApplicationPluginsProvider } from "../src/ApplicationPluginsContext";
import { ThemeProvider, lightTheme } from "../src/theme";
import { PinnedActionsProvider } from "../src/PinnedActionsContext";

jest.setTimeout(60_000);
let started: Awaited<ReturnType<typeof startChatOperationsBackend>>;
let proxy: Awaited<ReturnType<typeof startAcknowledgementProxy>>;
let backend: RestAgentBackend;
let rendered: ReturnType<typeof render> | null = null;

beforeAll(async () => {
  AppState.currentState = "active";
  started = await startChatOperationsBackend({
    messageCount: 8,
    firstMessageParts: [
      { type: "text", content: "Preserved part", metadata: { fixture: true } },
    ],
  });
  proxy = await startAcknowledgementProxy(started.server);
  backend = new RestAgentBackend({
    transport: new FetchTransport({ baseUrl: proxy.baseUrl }),
  });
});
afterEach(() => {
  rendered?.unmount();
  rendered = null;
  proxy?.setRule("none");
});
afterAll(async () => {
  await proxy?.stop();
  await started?.server.stop();
});

async function openChat() {
  const sessionId = started.sessions[0];
  const snapshot = await backend.listMessages(sessionId, {});
  rendered = render(
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <ChatWorkspaceProvider>
          <ApplicationPluginsProvider backend={backend} connectionId="local">
            <SessionChatScreen
              backend={backend}
              connectionId="local"
              sessionId={sessionId}
              sessionSummary={null}
              isActive
              cachedMessages={null}
              lastLoadedAt={null}
              cachedEventsCursorId={null}
              cachedActiveRequestId={null}
              onUpdateCache={() => {}}
              onUpdateSessionSummaries={() => {}}
              onBack={() => {}}
              onNavigateToSession={() => {}}
              initialComposeText=""
              initialScrollAnchor={null}
              initialRangeStartText="-50"
              initialRangeEndText=""
              onSaveComposeText={() => {}}
              onSaveScrollAnchor={() => {}}
              onSaveHistoryRange={() => {}}
              debugTimeline={[]}
              onAppendDebugTimelineEntry={() => {}}
            />
          </ApplicationPluginsProvider>
        </ChatWorkspaceProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
  await screen.findByTestId(
    `transcript-message-${
      snapshot.messages[snapshot.messages.length - 1].index
    }`,
    {},
    { timeout: 10_000 }
  );
  return sessionId;
}

test("modifies a message in the main and expanded composer without replacing the ordinary draft", async () => {
  const sessionId = await openChat();
  fireEvent.changeText(
    screen.getByTestId("message-composer-input"),
    "ordinary mobile draft"
  );
  fireEvent.press(
    within(screen.getByTestId("transcript-message-0")).getByLabelText("Modify")
  );
  expect(screen.getByText("Editing message [0]")).toBeTruthy();
  expect(screen.getByLabelText("Save edit")).toBeTruthy();
  fireEvent.press(screen.getByTestId("composer-cancel-edit"));
  expect(screen.queryByTestId("composer-edit-context")).toBeNull();
  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "ordinary mobile draft"
  );
  fireEvent.press(
    within(screen.getByTestId("transcript-message-0")).getByLabelText("Modify")
  );
  fireEvent.press(screen.getByTestId("composer-maximize"));
  fireEvent.changeText(
    screen.getByTestId("expanded-composer-input"),
    "modified mobile message"
  );
  fireEvent.press(screen.getByTestId("expanded-composer-collapse"));
  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "modified mobile message"
  );
  proxy.setRule("reject-edit-before", 1);
  fireEvent.press(screen.getByTestId("composer-send"));
  await waitFor(() =>
    expect(
      proxy.receipts.some((entry) => entry.stage === "rejected-edit")
    ).toBe(true)
  );
  await waitFor(() =>
    expect(screen.queryByTestId("composer-send-progress")).toBeNull()
  );
  expect(screen.getByTestId("composer-edit-context")).toBeTruthy();
  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "modified mobile message"
  );
  expect(
    (await backend.listMessages(sessionId, {})).messages[0].message.content
  ).toContain("Message 0");
  proxy.setRule("delay-edit");
  fireEvent.press(screen.getByTestId("composer-send"));
  await screen.findByTestId("composer-send-progress");
  expect(screen.getByTestId("chat-activity-label").props.children).toContain(
    "Saving message [0]"
  );
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 6000));
  });
  try {
    await waitFor(
      () => expect(screen.queryByTestId("composer-edit-context")).toBeNull(),
      { timeout: 15_000 }
    );
  } catch {
    throw new Error(
      `Edit did not finish. HTTP stages: ${JSON.stringify(
        proxy.receipts.slice(-20)
      )}`
    );
  }
  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "ordinary mobile draft"
  );
  const result = await backend.listMessages(sessionId, {});
  expect(result.messages[0].message.content).toBe("modified mobile message");
  expect(result.messages[0].message.role).toBe("user");
  expect(result.messages[0].message.metadata?.fixture).toBe(0);
  expect(result.messages[0].message.multipartContent).toEqual([
    { type: "text", content: "Preserved part", metadata: { fixture: true } },
  ]);
});

test("retries an accepted send after acknowledgement loss without duplicating its message", async () => {
  const sessionId = await openChat();
  const alert = jest.spyOn(Alert, "alert");
  proxy.setRule("drop-send-after");
  fireEvent.changeText(
    screen.getByTestId("message-composer-input"),
    "mobile uncertain send"
  );
  fireEvent.press(screen.getByTestId("composer-send"));
  await screen.findByTestId("chat-send-recovery", {}, { timeout: 10_000 });
  expect(alert).not.toHaveBeenCalled();
  await waitFor(
    async () => {
      const status = await backend.getSessionRequestStatuses([sessionId]);
      expect(status.statuses[0].state).not.toBe("running");
    },
    { timeout: 15_000 }
  );
  proxy.setRule("none");
  fireEvent.press(screen.getByTestId("chat-send-recovery-resend"));
  await waitFor(
    () => {
      expect(screen.queryByTestId("chat-send-recovery")).toBeNull();
      expect(screen.queryByTestId("composer-send-progress")).toBeNull();
    },
    { timeout: 10_000 }
  );
  const result = await backend.listMessages(sessionId, {});
  expect(
    result.messages.filter(
      (entry) => entry.message.content === "mobile uncertain send"
    )
  ).toHaveLength(1);
  expect(screen.getByTestId("message-composer-input").props.value).toBe("");
  expect(screen.queryByTestId("composer-send-progress")).toBeNull();
  alert.mockRestore();
});

test("dismisses failed-send recovery and keeps the ordinary draft", async () => {
  await openChat();
  proxy.setRule("drop-send-before");
  fireEvent.changeText(
    screen.getByTestId("message-composer-input"),
    "mobile cancel draft"
  );
  fireEvent.press(screen.getByTestId("composer-send"));
  await screen.findByTestId("chat-send-recovery");
  fireEvent.press(screen.getByTestId("chat-send-recovery-cancel"));
  expect(screen.queryByTestId("chat-send-recovery")).toBeNull();
  expect(screen.getByTestId("message-composer-input").props.value).toBe(
    "mobile cancel draft"
  );
});
