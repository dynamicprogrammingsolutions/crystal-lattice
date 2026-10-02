import { describe, expect, it, vi } from "vitest";

import type { AgentBackend } from "../backend/backend";
import {
  AgentsController,
  invalidateAgentsCache,
} from "./agentsController";

describe("AgentsController cache invalidation", () => {
  it("reloads agents after an embedded backend is reconstructed", async () => {
    const cacheKey = `embedded-${Date.now()}`;
    const firstBackend = {
      listAgents: vi.fn().mockResolvedValue(["local"]),
    } as unknown as AgentBackend;
    const secondBackend = {
      listAgents: vi.fn().mockResolvedValue(["local", "openai-codex"]),
    } as unknown as AgentBackend;

    const first = new AgentsController({ backend: firstBackend, cacheKey });
    expect(await first.load()).toEqual(["local"]);

    const cached = new AgentsController({ backend: secondBackend, cacheKey });
    expect(await cached.load()).toEqual(["local"]);
    expect(secondBackend.listAgents).not.toHaveBeenCalled();

    invalidateAgentsCache(cacheKey);
    const refreshed = new AgentsController({ backend: secondBackend, cacheKey });
    expect(await refreshed.load()).toEqual(["local", "openai-codex"]);
    expect(secondBackend.listAgents).toHaveBeenCalledOnce();
  });

  it("prefers ordered descriptors while preserving string ids", async () => {
    const cacheKey = `descriptors-${Date.now()}`;
    const backend = {
      listAgents: vi.fn().mockResolvedValue(["legacy"]),
      listAgentDescriptors: vi.fn().mockResolvedValue([
        {
          id: "claude",
          title: "Claude",
          description: "Claude-oriented tools.",
          order: 20,
        },
        {
          id: "codex",
          title: "Codex",
          description: "Codex-oriented tools.",
          order: 10,
        },
      ]),
    } as unknown as AgentBackend;

    const controller = new AgentsController({ backend, cacheKey });
    await expect(controller.load()).resolves.toEqual(["codex", "claude"]);
    await expect(controller.ensureDescriptorsLoaded()).resolves.toEqual([
      {
        id: "codex",
        title: "Codex",
        description: "Codex-oriented tools.",
        order: 10,
      },
      {
        id: "claude",
        title: "Claude",
        description: "Claude-oriented tools.",
        order: 20,
      },
    ]);
    expect(backend.listAgents).not.toHaveBeenCalled();
  });
});