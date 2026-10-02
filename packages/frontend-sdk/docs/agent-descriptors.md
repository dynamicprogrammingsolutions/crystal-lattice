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