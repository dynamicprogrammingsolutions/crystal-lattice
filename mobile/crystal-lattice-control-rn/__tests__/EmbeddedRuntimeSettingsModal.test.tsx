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
  defaultAgent: "openai-codex",
  reviewerVisible: false,
  profileOrder: [
    "openai",
    "compatible",
    "openrouter",
    "anthropic",
    "reviewer",
  ],
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
  jest
    .mocked(configureEmbeddedPythonRuntime)
    .mockImplementation(async (update) => ({
      ...configuration,
      defaultAgent: update.defaultAgent ?? configuration.defaultAgent,
      reviewerVisible:
        update.reviewerVisible ?? configuration.reviewerVisible,
      providers: Object.fromEntries(
        Object.entries(configuration.providers).map(([profileId, profile]) => {
          const profileUpdate = update.providers?.[
            profileId as keyof typeof configuration.providers
          ];
          return [
            profileId,
            {
              ...profile,
              enabled: profileUpdate?.enabled ?? profile.enabled,
              baseUrl: profileUpdate?.baseUrl ?? profile.baseUrl,
              model: profileUpdate?.model ?? profile.model,
              authMode: profileUpdate?.authMode ?? profile.authMode,
              hasApiKey:
                profileUpdate?.clearApiKey === true
                  ? false
                  : Boolean(profileUpdate?.apiKey) || profile.hasApiKey,
            },
          ];
        })
      ) as EmbeddedRuntimePublicConfiguration["providers"],
    }));
  jest.mocked(executeEmbeddedRuntimeApplicationAction).mockResolvedValue({
    auth_status: {
      state: "pending",
      verification_url: "https://auth.openai.test/device",
      user_code: "ABCD-EFGH",
    },
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

test("tests the current candidate without persisting it", async () => {
  const { onSaved, screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-openai")).toBeTruthy()
  );

  fireEvent.press(screen.getByTestId("embedded-provider-openai-test"));

  await waitFor(() =>
    expect(validateEmbeddedPythonRuntimeConfiguration).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultAgent: "openai-codex",
        reviewerVisible: false,
        profileId: "openai",
        providers: expect.objectContaining({
          openai: expect.objectContaining({
            enabled: true,
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
  ).toBe(false);
  expect(configureEmbeddedPythonRuntime).not.toHaveBeenCalled();
  expect(onSaved).not.toHaveBeenCalled();
});

test("autosaves provider edits and default selection", async () => {
  const { onSaved, screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-openrouter")).toBeTruthy()
  );

  fireEvent.changeText(
    screen.getByTestId("embedded-provider-openrouter-model"),
    "openrouter/test-model"
  );
  fireEvent.press(
    screen.getByTestId("embedded-provider-openrouter-default")
  );

  await waitFor(
    () =>
      expect(configureEmbeddedPythonRuntime).toHaveBeenCalledWith(
        expect.objectContaining({
          defaultAgent: "openrouter-claude",
          reviewerVisible: false,
          providers: expect.objectContaining({
            openrouter: expect.objectContaining({
              model: "openrouter/test-model",
            }),
          }),
        })
      ),
    { timeout: 2500 }
  );
  await waitFor(() => expect(onSaved).toHaveBeenCalled());
  expect(screen.queryByTestId("embedded-runtime-settings-save")).toBeNull();
});

test("keeps reviewer hidden until enabled and exposes only its API key", async () => {
  const { screen } = renderModal();
  await waitFor(() =>
    expect(screen.getByTestId("embedded-reviewer-visible")).toBeTruthy()
  );
  expect(screen.queryByTestId("embedded-provider-reviewer")).toBeNull();

  fireEvent(screen.getByTestId("embedded-reviewer-visible"), "valueChange", true);

  await waitFor(() =>
    expect(screen.getByTestId("embedded-provider-reviewer")).toBeTruthy()
  );
  expect(
    screen.queryByTestId("embedded-provider-reviewer-enabled")
  ).toBeNull();
  expect(
    screen.queryByTestId("embedded-provider-reviewer-base-url")
  ).toBeNull();
  expect(
    screen.queryByTestId("embedded-provider-reviewer-model")
  ).toBeNull();
  expect(
    screen.queryByTestId("embedded-provider-reviewer-tls-ca-bundle")
  ).toBeNull();
  expect(
    screen.getByTestId("embedded-provider-reviewer-api-key")
  ).toBeTruthy();
  const providerChildren = screen.getByTestId("embedded-provider-list").props
    .children as React.ReactElement<{ testID?: string }>[];
  expect(providerChildren.at(-1)?.props.testID).toBe(
    "embedded-provider-reviewer"
  );

  await waitFor(
    () =>
      expect(configureEmbeddedPythonRuntime).toHaveBeenCalledWith(
        expect.objectContaining({ reviewerVisible: true })
      ),
    { timeout: 2500 }
  );
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
    screen.getByTestId("embedded-provider-openai-chatgpt-auth-state")
  ).toHaveTextContent("ChatGPT status: pending");
  expect(
    screen.getByTestId("embedded-provider-openai-chatgpt-login-url")
  ).toHaveTextContent("https://auth.openai.test/device");
  expect(
    screen.getByTestId("embedded-provider-openai-chatgpt-login-code")
  ).toHaveTextContent("ABCD-EFGH");
  expect(
    screen.getByTestId("action-display-action-open-chatgpt-login-link")
  ).toBeTruthy();
  expect(
    screen.getByTestId("action-display-action-copy-chatgpt-login-code")
  ).toBeTruthy();

  jest.mocked(executeEmbeddedRuntimeApplicationAction).mockResolvedValueOnce({
    auth_status: { state: "authenticated" },
    display: {
      format: "markdown",
      title: "ChatGPT Login Status",
      body: "ChatGPT login is active.",
    },
  });
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
  await waitFor(() =>
    expect(
      screen.getByTestId("embedded-provider-openai-chatgpt-auth-state")
    ).toHaveTextContent("ChatGPT status: authenticated")
  );
  expect(
    screen.queryByTestId("embedded-provider-openai-chatgpt-login-code")
  ).toBeNull();
  expect(
    screen.getByTestId("action-display-action-open-chatgpt-login-link")
  ).toBeTruthy();
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