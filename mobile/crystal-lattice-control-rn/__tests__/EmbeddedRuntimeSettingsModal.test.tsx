import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";

import EmbeddedRuntimeSettingsModal from "../src/embeddedRuntime/EmbeddedRuntimeSettingsModal";
import {
  configureEmbeddedPythonRuntime,
  executeEmbeddedRuntimeApplicationAction,
  getEmbeddedPythonRuntimeConfiguration,
  validateEmbeddedPythonRuntimeConfiguration,
  type EmbeddedRuntimePublicConfiguration,
} from "../src/embeddedRuntime/embeddedPythonRuntime";
import { lightTheme, ThemeProvider } from "../src/theme";

jest.mock("../src/embeddedRuntime/embeddedPythonRuntime", () => ({
  configureEmbeddedPythonRuntime: jest.fn(),
  executeEmbeddedRuntimeApplicationAction: jest.fn(),
  getEmbeddedPythonRuntimeConfiguration: jest.fn(),
  validateEmbeddedPythonRuntimeConfiguration: jest.fn(),
}));

const configuration: EmbeddedRuntimePublicConfiguration = {
  version: 3,
  defaultAgent: "reviewer-codex",
  proxyUrl: "http://127.0.0.1:3000/v1",
  model: "qwen3.5:0.8b",
  hasApiKey: true,
  providers: {
    compatible: {
      id: "compatible",
      label: "OpenAI-compatible",
      agentId: "compatible-claude",
      toolFamily: "claude-like",
      enabled: false,
      baseUrl: "http://127.0.0.1:3000/v1",
      model: "qwen3.5:0.8b",
      hasApiKey: false,
    },
    reviewer: {
      id: "reviewer",
      label: "OpenAI Responses reviewer",
      agentId: "reviewer-codex",
      toolFamily: "codex-like",
      enabled: true,
      baseUrl:
        "https://ireland-s1.dynamicprogrammingsolutions.com:3443/v1",
      model: "gpt-5.6-luna",
      tlsCaBundle: "/runtime/reviewer-proxy-ca.pem",
      hasApiKey: true,
    },
    openai: {
      id: "openai",
      label: "OpenAI Responses",
      agentId: "openai-codex",
      toolFamily: "codex-like",
      enabled: false,
      baseUrl: "https://api.openai.com/v1",
      model: "gpt-5.6-luna",
      authMode: "api",
      hasApiKey: false,
    },
    openrouter: {
      id: "openrouter",
      label: "OpenRouter",
      agentId: "openrouter-claude",
      toolFamily: "claude-like",
      enabled: false,
      baseUrl: "https://openrouter.ai/api/v1",
      model: "anthropic/claude-haiku-4.5",
      hasApiKey: false,
    },
    anthropic: {
      id: "anthropic",
      label: "Anthropic",
      agentId: "anthropic-claude",
      toolFamily: "claude-like",
      enabled: false,
      baseUrl: "https://api.anthropic.com",
      model: "claude-haiku-4-5-20251001",
      hasApiKey: false,
    },
  },
};

function renderModal(onSaved = jest.fn()) {
  return {
    onSaved,
    screen: render(
      <ThemeProvider theme={lightTheme}>
        <EmbeddedRuntimeSettingsModal
          visible
          onRequestClose={() => {}}
          onSaved={onSaved}
        />
      </ThemeProvider>
    ),
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  jest
    .mocked(getEmbeddedPythonRuntimeConfiguration)
    .mockResolvedValue(configuration);
  jest
    .mocked(validateEmbeddedPythonRuntimeConfiguration)
    .mockResolvedValue({
      status: "ok",
      profile_id: "openai",
      model: "gpt-5.6-luna",
    });
  jest.mocked(configureEmbeddedPythonRuntime).mockResolvedValue({
    ...configuration,
    defaultAgent: "openai-codex",
    providers: {
      ...configuration.providers,
      openai: {
        ...configuration.providers.openai,
        enabled: true,
        hasApiKey: true,
      },
    },
  });
  jest.mocked(executeEmbeddedRuntimeApplicationAction).mockResolvedValue({
    display: {
      format: "markdown",
      title: "ChatGPT Login",
      body: "Open the login URL and enter `ABCD-EFGH`.",
      presentation: "inline",
      actions: [
        {
          kind: "open_url",
          id: "open-chatgpt-login-link",
          label: "Open link",
          url: "https://auth.openai.test/device",
        },
        {
          kind: "copy_text",
          id: "copy-chatgpt-login-code",
          label: "Copy code",
          text: "ABCD-EFGH",
        },
        {
          kind: "run_action",
          id: "check-chatgpt-login-status",
          label: "Check status",
          plugin: "chatgpt_auth",
          action_id: "check_status",
          fixed_params: {},
          preserve_display: true,
        },
      ],
    },
  });
});

test("tests a candidate before saving and persists the selected default", async () => {
  const { onSaved, screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-openai")).toBeTruthy()
  );

  fireEvent.changeText(
    screen.getByTestId("embedded-provider-openai-api-key"),
    "temporary-key"
  );
  fireEvent.press(screen.getByTestId("embedded-provider-openai-test"));

  await waitFor(() =>
    expect(validateEmbeddedPythonRuntimeConfiguration).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultAgent: "reviewer-codex",
        profileId: "openai",
        providers: expect.objectContaining({
          openai: expect.objectContaining({
            enabled: true,
            apiKey: "temporary-key",
            authMode: "api",
          }),
        }),
      })
    )
  );
  expect(configureEmbeddedPythonRuntime).not.toHaveBeenCalled();
  expect(
    screen.getByTestId("embedded-provider-openai-validation").props.children
  ).toBe("Connected to gpt-5.6-luna");
  expect(
    screen.getByTestId("embedded-provider-openai-enabled").props.value
  ).toBe(true);

  fireEvent.press(screen.getByTestId("embedded-runtime-settings-save"));
  await waitFor(() =>
    expect(configureEmbeddedPythonRuntime).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultAgent: "openai-codex",
        providers: expect.objectContaining({
          openai: expect.objectContaining({
            enabled: true,
            apiKey: "temporary-key",
          }),
        }),
      })
    )
  );
  await waitFor(() => expect(onSaved).toHaveBeenCalled());
});

test("runs plugin-driven ChatGPT login actions from provider settings", async () => {
  const { screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-openai")).toBeTruthy()
  );

  expect(
    screen.queryByTestId("embedded-provider-openai-auth-auto")
  ).toBeNull();
  fireEvent.press(screen.getByTestId("embedded-provider-openai-auth-chatgpt"));

  expect(
    screen.queryByTestId("embedded-provider-openai-api-key")
  ).toBeNull();
  fireEvent.press(
    screen.getByTestId("embedded-provider-openai-chatgpt-login_start")
  );

  await waitFor(() =>
    expect(executeEmbeddedRuntimeApplicationAction).toHaveBeenCalledWith({
      pluginId: "chatgpt_auth",
      actionId: "login_start",
      actionOwner: undefined,
      inputs: undefined,
    })
  );
  expect(
    screen.getByTestId("action-display-action-open-chatgpt-login-link")
  ).toBeTruthy();
  expect(
    screen.getByTestId("action-display-action-copy-chatgpt-login-code")
  ).toBeTruthy();

  fireEvent.press(
    screen.getByTestId("action-display-action-check-chatgpt-login-status")
  );
  await waitFor(() =>
    expect(executeEmbeddedRuntimeApplicationAction).toHaveBeenLastCalledWith({
      pluginId: "chatgpt_auth",
      actionId: "check_status",
      actionOwner: undefined,
      inputs: {},
    })
  );
});

test("shows candidate validation failure without persisting it", async () => {
  jest
    .mocked(validateEmbeddedPythonRuntimeConfiguration)
    .mockRejectedValue(new Error("The API key was rejected."));
  const { screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-anthropic")).toBeTruthy()
  );

  fireEvent.press(screen.getByTestId("embedded-provider-anthropic-test"));

  await waitFor(() =>
    expect(
      screen.getByTestId("embedded-provider-anthropic-validation").props
        .children
    ).toBe("The API key was rejected.")
  );
  expect(configureEmbeddedPythonRuntime).not.toHaveBeenCalled();
});