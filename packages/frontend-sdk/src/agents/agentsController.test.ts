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
});