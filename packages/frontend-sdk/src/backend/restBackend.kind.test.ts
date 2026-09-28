import { describe, expect, it } from "vitest";

import type { Transport } from "../transport/transport";
import { RestAgentBackend } from "./restBackend";

const transport: Transport = {
  async request() {
    return { status: 200, data: {} };
  },
};

describe("RestAgentBackend kind", () => {
  it("defaults to rest and supports an in-process transport identity", () => {
    expect(new RestAgentBackend({ transport }).kind).toBe("rest");
    expect(new RestAgentBackend({ transport, kind: "inProcess" }).kind).toBe(
      "inProcess",
    );
  });
});
