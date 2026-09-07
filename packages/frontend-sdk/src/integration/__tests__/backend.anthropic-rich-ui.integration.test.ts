import http from "node:http";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { RestAgentBackend } from "../../backend/restBackend";
import { SessionSettingsController } from "../../sessionSettings/sessionSettingsController";
import { FetchTransport } from "../../transport/fetchTransport";
import {
  findRepoRoot,
  getFreePort,
  startBackendServer,
  type StartedServer,
} from "../harness";

describe("Anthropic rich model UI through the public backend", () => {
  let started: StartedServer | null = null;
  let modelServer: http.Server | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
    if (modelServer) {
      await new Promise<void>((resolve) => modelServer!.close(() => resolve()));
      modelServer = null;
    }
  });

  it("discovers models and mutates the ordinary model override through RestAgentBackend", async () => {
    const repoRoot = findRepoRoot(process.cwd());
    const modelPort = await getFreePort();
    modelServer = http.createServer((request, response) => {
      if (request.method === "GET" && request.url?.startsWith("/v1/models")) {
        response.writeHead(200, { "content-type": "application/json" });
        response.end(
          JSON.stringify({
            data: [
              {
                type: "model",
                id: "claude-a",
                display_name: "Claude A",
                created_at: "2026-01-01T00:00:00Z",
              },
              {
                type: "model",
                id: "claude-b",
                display_name: "Claude B",
                created_at: "2026-01-02T00:00:00Z",
              },
            ],
            has_more: false,
            first_id: "claude-a",
            last_id: "claude-b",
          }),
        );
        return;
      }
      response.writeHead(404, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: { message: "not found" } }));
    });
    await new Promise<void>((resolve) => {
      modelServer!.listen(modelPort, "127.0.0.1", () => resolve());
    });

    const config = {
      plugin_cache_dir: path.join(
        repoRoot,
        "tmp",
        "anthropic-rich-ui-plugin-cache",
      ),
      plugins: [
        "anthropic_plugins.provider.AnthropicProvider",
        `path:${path.join(repoRoot, "plugins", "session-status-app")}`,
        `path:${path.join(repoRoot, "plugins", "dummy-rich-config-ui")}`,
      ],
      providers: {
        anthropic_test: {
          provider: "anthropic",
          api_key: "integration-test-key",
          base_url: `http://127.0.0.1:${modelPort}`,
          model: "claude-a",
          timeout: 5,
          max_retries: 0,
        },
      },
      agents: {
        default: {
          provider: "anthropic_test",
          enabled_plugins: ["dummy_rich_config_ui"],
        },
      },
    };

    const previousPython = process.env.PYTHON;
    process.env.PYTHON = "python";
    try {
      started = await startBackendServer({
        config,
        startupTimeoutMs: 30000,
        env: {
          PYTHONPATH: [
            path.join(repoRoot, "core", "python"),
            path.join(repoRoot, "application", "python"),
            path.join(repoRoot, "plugins", "anthropic-compatible", "src"),
            path.join(repoRoot, "plugins", "session-status-app", "src"),
            path.join(repoRoot, "plugins", "dummy-rich-config-ui", "src"),
          ].join(path.delimiter),
        },
      });
    } finally {
      if (previousPython === undefined) {
        delete process.env.PYTHON;
      } else {
        process.env.PYTHON = previousPython;
      }
    }

    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: "default" });
    const sessionId = created.session.session_id;
    const controller = new SessionSettingsController({
      backend,
      cacheKey: "anthropic-rich-ui",
      sessionId,
    });

    await controller.load();
    const model = controller
      .getSnapshot()
      .elements.find((element) => element.key === "model");
    expect(model).toMatchObject({
      ui_type: "config",
      type: "dropdown",
      key: "model",
      icon: "cpu",
      custom_value: {
        enabled: true,
      },
      options: [
        { value: "claude-a", label: "Claude A" },
        { value: "claude-b", label: "Claude B" },
      ],
      rich_ui: {
        kind: "dropdown",
        label: "Model",
        placements: ["composer"],
        default_pinned: true,
        show_label: false,
        custom_value: {
          enabled: true,
        },
      },
    });
    const appearance = controller
      .getSnapshot()
      .elements.find((element) => element.key === "dummy_rich_ui_appearance");
    expect(appearance).toMatchObject({
      ui_type: "config",
      type: "select",
      icon: "sliders",
      rich_ui: {
        kind: "dropdown",
        placements: ["composer", "session_header"],
      },
    });
    expect(
      (appearance?.options ?? []).map((option: any) => option.tone),
    ).toEqual([
      "primary",
      "highlight",
      "warning",
      "success",
      "danger",
      "muted",
    ]);

    const sessionActions =
      await backend.getSessionApplicationUiSchema(sessionId);
    const statusAction = sessionActions.find(
      (element) =>
        element.ui_type === "session_action" &&
        element.id === "set_session_status",
    );
    expect(statusAction).toMatchObject({
      action_id: "set_session_status",
      rich_ui: {
        kind: "list",
        placements: ["session_header"],
        value_path: "metadata.status",
      },
    });

    await controller.patchOverride("model", "claude-b");
    expect((await backend.getSessionOverrides(sessionId)).model).toBe(
      "claude-b",
    );

    await controller.patchOverride("model", "vendor/custom-model");
    expect((await backend.getSessionOverrides(sessionId)).model).toBe(
      "vendor/custom-model",
    );

    await controller.patchOverride("dummy_rich_ui_appearance", "warning");
    await controller.patchOverride("dummy_rich_ui_toggle", true);
    expect(await backend.getSessionOverrides(sessionId)).toMatchObject({
      model: "vendor/custom-model",
      dummy_rich_ui_appearance: "warning",
      dummy_rich_ui_toggle: true,
    });

    await controller.deleteOverride("dummy_rich_ui_appearance");
    await controller.deleteOverride("dummy_rich_ui_toggle");
    await controller.deleteOverride("model");
    expect(await backend.getSessionOverrides(sessionId)).toEqual({});
    expect((await backend.getSessionBaseConfig(sessionId)).model).toBe(
      "claude-a",
    );

    controller.dispose();
  }, 60000);
});
