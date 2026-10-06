# Agent descriptors

The backend keeps stable agent IDs separate from user-facing presentation.

```ts
export interface AgentDescriptor {
  id: string;
  title: string;
  description: string;
  order: number;
}
```

`AgentBackend.listAgents()` remains the compatibility API and returns stable
string IDs.

Backends that support display metadata expose:

```ts
listAgentDescriptors?(): Promise<AgentDescriptor[]>;
```

`RestAgentBackend` reads both values from `GET /agents`. The agents controller
prefers descriptors when available, sorts by `order` with stable response
ordering as a tiebreaker, and derives its compatibility `agents` list from
descriptor IDs. If a backend does not expose descriptors, the controller
creates fallback descriptors whose title is the ID and whose description is
empty.

Use descriptor title and description for selection UI. Continue using
descriptor `id` for:

- session creation;
- agent switching;
- session metadata;
- cache keys;
- deep links and interoperability.

Callers that only need IDs can keep using:

```ts
await controller.ensureLoaded();
```

Selection UI can use:

```ts
await controller.ensureDescriptorsLoaded();
```

## Effective agent defaults

Backends may also expose a read-only plugin preview:

```ts
listAgentPlugins?(agentId: string): Promise<AgentPluginEntry[]>;
```

`RestAgentBackend` reads this from
`GET /agents/{agent_id}/plugins`. Each entry contains only safe plugin
identity/state fields:

- stable plugin ID and kind;
- optional class/name metadata;
- default-enabled state;
- effective active state for the agent's base configuration;
- `agent` or `implicit` source.

Configuration values and credentials are not part of this contract.

`AgentsController.ensurePluginsLoaded(agentId)` caches the normalized result
per connection cache key and agent ID. Concurrent requests for the same
profile share one in-flight request. `invalidateAgentsCache(cacheKey)` clears
both descriptor and plugin-preview caches.

The method is optional so clients remain compatible with older or
non-HTTP backends. Selection must remain usable when preview support is
missing or when a preview request fails.