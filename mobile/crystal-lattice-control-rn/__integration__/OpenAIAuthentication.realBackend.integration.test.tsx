import React from "react";
import { fireEvent, screen, waitFor } from "@testing-library/react-native";

import SessionSettingsModal from "../src/components/SessionSettingsModal";
import { renderWithMobileProviders } from "../src/testUtils/renderWithMobileProviders";
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from "./support/mobileComponentBackend";

describe("OpenAI authentication through production session settings and HTTP", () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it.each(["api", "chatgpt"] as const)(
    "overrides and resets the %s default without changing base configuration",
    async (defaultMode) => {
      const override = defaultMode === "api" ? "chatgpt" : "api";
      started = await startMobileComponentBackend({
        config: {
          providers: {
            openai: {
              provider: "openai_responses",
              provider_transport: "requests",
              api_key: "fixture-key",
              base_url: "http://127.0.0.1:1/v1",
              model: "gpt-5.6-luna",
              auth_mode: defaultMode,
              auth_mode_options: ["api", "chatgpt"],
            },
          },
          plugins: [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension",
            "openai_responses_plugins.openai_responses_fast_mode_extension.OpenAIResponsesFastModeExtension",
          ],
          agents: {
            openai: {
              provider: "openai",
              extensions: [
                "openai_responses_flex_processing",
                "openai_responses_fast_mode",
              ],
            },
          },
        },
      });
      const backend = started.backend;
      const sessionId = await createMobileComponentSession(backend, "openai");
      const host = renderWithMobileProviders(
        <SessionSettingsModal
          backend={backend}
          cacheKey={`auth-${defaultMode}`}
          sessionId={sessionId}
          visible
          onRequestClose={() => {}}
        />
      );
      expect(screen.queryByTestId("session-setting-select-auth_mode-auto")).toBeNull();
      fireEvent.press(await screen.findByTestId(`session-setting-select-auth_mode-${override}`));
      await waitFor(async () => {
        expect((await backend.getSessionOverrides(sessionId)).auth_mode).toBe(override);
      });
      expect((await backend.getSessionBaseConfig(sessionId)).auth_mode).toBe(defaultMode);
      const schema = await backend.getSessionUiSchema(sessionId);
      expect(schema.some((element) => element.key === "enable_flex_processing"))
        .toBe(override === "api");
      expect(schema.some((element) => element.key === "enable_fast_mode"))
        .toBe(override === "api");
      fireEvent.press(await screen.findByTestId("session-setting-reset-auth_mode"));
      await waitFor(async () => {
        expect(await backend.getSessionOverrides(sessionId)).not.toHaveProperty("auth_mode");
      });
      expect((await backend.getSessionBaseConfig(sessionId)).auth_mode).toBe(defaultMode);
      host.unmount();
    }
  );
});