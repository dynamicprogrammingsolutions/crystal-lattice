import React from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Pressable, Text } from "react-native";
import { act, fireEvent, render, waitFor } from "@testing-library/react-native";

import {
  PinnedActionsProvider,
  usePersistentPinnedActionsFromContext,
} from "../src/PinnedActionsContext";

function Probe({ initialPinned }: { initialPinned: string[] }) {
  const { loaded, pinned, setPinned } = usePersistentPinnedActionsFromContext(
    "rich-session-actions",
    initialPinned
  );
  return (
    <>
      <Text testID="pinned-actions-probe">
        {loaded ? JSON.stringify(pinned) : "loading"}
      </Text>
      <Pressable
        testID="pinned-actions-set-local"
        onPress={() => setPinned(["localWatchlist"])}
      />
    </>
  );
}

function renderProbe(initialPinned: string[]) {
  return render(
    <PinnedActionsProvider>
      <Probe initialPinned={initialPinned} />
    </PinnedActionsProvider>
  );
}

beforeEach(async () => {
  await (AsyncStorage as any).clear();
});

test("adopts rich defaults that arrive after absent storage resolves", async () => {
  const rendered = renderProbe(["agentSwitch"]);
  await waitFor(() => {
    expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
      '["agentSwitch"]'
    );
  });

  rendered.rerender(
    <PinnedActionsProvider>
      <Probe
        initialPinned={[
          "agentSwitch",
          "toggle_session_pinned",
          "toggle_session_archived",
        ]}
      />
    </PinnedActionsProvider>
  );

  await waitFor(() => {
    expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
      '["agentSwitch","toggle_session_pinned","toggle_session_archived"]'
    );
  });
});

test("preserves a stored empty preference when rich defaults change", async () => {
  await (AsyncStorage as any).setItem("rich-session-actions", "[]");
  const rendered = renderProbe(["toggle_session_pinned"]);
  await waitFor(() => {
    expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
      "[]"
    );
  });

  rendered.rerender(
    <PinnedActionsProvider>
      <Probe
        initialPinned={["toggle_session_pinned", "toggle_session_archived"]}
      />
    </PinnedActionsProvider>
  );
  await waitFor(() => {
    expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
      "[]"
    );
  });
});

test("keeps a user pin change made while storage hydration is in flight", async () => {
  let resolveStored: (value: string | null) => void = () => {};
  const stored = new Promise<string | null>((resolve) => {
    resolveStored = resolve;
  });
  const getItem = jest
    .spyOn(AsyncStorage, "getItem")
    .mockImplementation(async (key) =>
      key === "rich-session-actions" ? stored : null
    );
  const rendered = renderProbe(["reload"]);
  await waitFor(() => expect(getItem).toHaveBeenCalled());

  fireEvent.press(rendered.getByTestId("pinned-actions-set-local"));
  await waitFor(() =>
    expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
      '["localWatchlist"]'
    )
  );

  await act(async () => {
    resolveStored(null);
    await stored;
  });
  expect(rendered.getByTestId("pinned-actions-probe").props.children).toBe(
    '["localWatchlist"]'
  );
  getItem.mockRestore();
});
