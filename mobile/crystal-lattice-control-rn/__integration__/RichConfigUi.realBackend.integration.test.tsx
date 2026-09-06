import React from "react";
import { fireEvent, screen, waitFor } from "@testing-library/react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { ApplicationPluginsProvider } from "@crystal-lattice/frontend-sdk-react";

import { PinnedActionsProvider } from "../src/PinnedActionsContext";
import SessionChatScreen from "../src/SessionChatScreen";
import GlobalDisplayLayer from "../src/components/GlobalDisplayLayer";
import { renderWithMobileProviders } from "../src/testUtils/renderWithMobileProviders";
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from "./support/mobileComponentBackend";

const SERVER_CONFIG = {
  providers: {
    test_provider: {
      provider: "deterministic_stream",
      model: "test-model",
      stream_chunk_count: 1,
      stream_chunk_delay_ms: 0,
    },
  },
  plugins: [
    "plugins.deterministic_stream_provider.DeterministicStreamProvider",
    "path:${env:REPO_ROOT}/plugins/dummy-rich-config-ui",
  ],
  agents: {
    default: {
      provider: "test_provider",
      enabled_plugins: ["dummy_rich_config_ui"],
    },
  },
};

describe("dummy rich config UI real-backend component integration", () => {
  let started: StartedMobileComponentBackend | null = null;

  beforeEach(async () => {
    await AsyncStorage.clear();
  });

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it("loads the real dummy plugin through HTTP and mutates its rich controls", async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const sessionId = await createMobileComponentSession(started.backend);
    const sessionSummary = await started.backend.getSessionSummary(sessionId);

    renderWithMobileProviders(
      <SafeAreaProvider>
        <PinnedActionsProvider>
          <ApplicationPluginsProvider
            backend={started.backend}
            connectionId="dummy-rich-ui-real-backend"
          >
            <GlobalDisplayLayer
              backend={started.backend}
              connectionId="dummy-rich-ui-real-backend"
            >
              <SessionChatScreen
                backend={started.backend}
                connectionId="dummy-rich-ui-real-backend"
                isActive
                sessionId={sessionId}
                sessionSummary={sessionSummary}
                cachedMessages={[]}
                lastLoadedAt={1}
                cachedEventsCursorId="0"
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
            </GlobalDisplayLayer>
          </ApplicationPluginsProvider>
        </PinnedActionsProvider>
      </SafeAreaProvider>
    );

    fireEvent.press(
      await screen.findByTestId("composer-rich-config-dummy_rich_ui_appearance")
    );
    fireEvent.press(
      await screen.findByTestId("options-picker-declared-warning")
    );

    await waitFor(async () => {
      expect(
        (await started!.backend.getSessionOverrides(sessionId))
          .dummy_rich_ui_appearance
      ).toBe("warning");
    });

    fireEvent.press(
      await screen.findByTestId("composer-rich-config-dummy_rich_ui_toggle")
    );
    await waitFor(async () => {
      expect(
        (await started!.backend.getSessionOverrides(sessionId))
          .dummy_rich_ui_toggle
      ).toBe(true);
    });
  });
});
