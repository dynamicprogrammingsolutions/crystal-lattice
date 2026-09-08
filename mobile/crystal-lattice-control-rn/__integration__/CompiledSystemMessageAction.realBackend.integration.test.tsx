import React from "react";
import { fireEvent, screen } from "@testing-library/react-native";

import {
  runApplicationAction,
  type ActionUiElement,
} from "@crystal-lattice/frontend-sdk";

import ActionResultModal from "../src/components/ActionResultModal";
import { renderWithMobileProviders } from "../src/testUtils/renderWithMobileProviders";
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from "./support/mobileComponentBackend";

const LONG_PROMPT = Array.from(
  { length: 300 },
  (_, index) => `Instruction line ${index}: verify the compiled prompt.`
).join("\n");

const SERVER_CONFIG = {
  providers: {
    echo: {
      provider: "echo_openai_like",
      model: "test-model",
      system_message_as_instructions: true,
      system_message: {
        template: "# Compiled system message\n\n{{LONG_PROMPT}}",
        variables: {
          LONG_PROMPT,
        },
      },
    },
  },
  plugins: [
    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
    "path:${env:REPO_ROOT}/plugins/feature-system-message",
  ],
  agents: {
    default: { provider: "echo" },
  },
  application: {},
};

describe("compiled system message action real-backend integration", () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it("executes the real feature action and scrolls its lengthy modal body", async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const sessionId = await createMobileComponentSession(started.backend);
    const uiSchema = await started.backend.getSessionUiSchema(sessionId);
    const element = uiSchema.find(
      (item: any) => item.id === "show_compiled_system_message"
    ) as ActionUiElement | undefined;

    expect(element).toBeTruthy();
    expect(element?.action_owner).toBe("feature");

    const result = await runApplicationAction({
      backend: started.backend,
      element: element!,
      actionsById: {},
      context: { sessionId },
    });

    expect(result.ok).toBe(true);
    expect(result.effects).toEqual([]);
    expect(result.display?.body).toBe(
      `# Compiled system message\n\n${LONG_PROMPT}`
    );

    renderWithMobileProviders(
      <ActionResultModal
        visible
        display={result.display ?? null}
        testID="compiled-system-message-modal"
        onRequestClose={() => {}}
      />
    );

    expect(screen.getByText("Compiled system message")).toBeTruthy();
    expect(screen.getByText(result.display!.body)).toBeTruthy();
    const bodyScroll = screen.getByTestId("compiled-system-message-modal-body");
    expect(bodyScroll.props.scrollEnabled).not.toBe(false);
    fireEvent.scroll(bodyScroll, {
      nativeEvent: {
        contentOffset: { x: 0, y: 500 },
        contentSize: { width: 500, height: 6000 },
        layoutMeasurement: { width: 500, height: 400 },
      },
    });
  }, 60000);
});
