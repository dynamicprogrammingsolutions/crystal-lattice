import {
  RestAgentBackend,
  type AgentBackend,
} from "@crystal-lattice/frontend-sdk";

import { EmbeddedRuntimeTransport } from "./EmbeddedRuntimeTransport";

export interface EmbeddedRuntimeBackend {
  backend: AgentBackend;
  transport: EmbeddedRuntimeTransport;
}

export function createEmbeddedRuntimeBackend(): EmbeddedRuntimeBackend {
  const transport = new EmbeddedRuntimeTransport();
  return {
    backend: new RestAgentBackend({
      transport,
      kind: "inProcess",
    }),
    transport,
  };
}
