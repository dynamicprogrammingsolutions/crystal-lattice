import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";

import EmbeddedRuntimeSettingsModal from "../src/embeddedRuntime/EmbeddedRuntimeSettingsModal";
import {
  configureEmbeddedPythonRuntime,
  getEmbeddedPythonRuntimeConfiguration,
  validateEmbeddedPythonRuntimeConfiguration,
  type EmbeddedRuntimePublicConfiguration,
} from "../src/embeddedRuntime/embeddedPythonRuntime";
import { lightTheme, ThemeProvider } from "../src/theme";

jest.mock("../src/embeddedRuntime/embeddedPythonRuntime", () => ({
  configureEmbeddedPythonRuntime: jest.fn(),
  getEmbeddedPythonRuntimeConfiguration: jest.fn(),
  validateEmbeddedPythonRuntimeConfiguration: jest.fn(),
}));

const configuration: EmbeddedRuntimePublicConfiguration = {
  version: 2,
  defaultAgent: "reviewer-claude",
  proxyUrl: "http://127.0.0.1:3000/v1",
  model: "qwen3.5:0.8b",
  hasApiKey: true,
  providers: {
    reviewer: {
      id: "reviewer",
      label: "OpenAI-compatible reviewer",
      agentId: "reviewer-claude",
      toolFamily: "claude-like",
      enabled: true,
      baseUrl: "http://127.0.0.1:3000/v1",
      model: "qwen3.5:0.8b",
      tlsCaBundle: "",
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
  fireEvent.press(screen.getByTestId("embedded-provider-openai-auth-auto"));
  fireEvent.press(screen.getByTestId("embedded-provider-openai-test"));

  await waitFor(() =>
    expect(validateEmbeddedPythonRuntimeConfiguration).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultAgent: "reviewer-claude",
        profileId: "openai",
        providers: expect.objectContaining({
          openai: expect.objectContaining({
            enabled: true,
            apiKey: "temporary-key",
            authMode: "auto",
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