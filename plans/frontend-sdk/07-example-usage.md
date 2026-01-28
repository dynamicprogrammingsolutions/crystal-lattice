# Example usage patterns

These are sketches showing what a thin frontend should look like once controllers are extracted.

## 1) Mobile RN / Desktop RN

Frontend responsibilities:

- Render UI (screens/components)
- Provide platform services (storage, clipboard, system dialogs)
- Choose a connection method and build an `AgentBackend`

SDK responsibilities:

- Chat/session/plugin workflows

Pseudo-code:

```ts
import { RestAgentBackend, FetchTransport, ChatController } from '@crystal-lattice/frontend-sdk';
import { useSubscribableSnapshot } from '@crystal-lattice/frontend-sdk-react';

const transport = new FetchTransport({ baseUrl: 'http://192.168.1.10:8000' });
const backend = new RestAgentBackend({ transport });

const chat = new ChatController({ backend, sessionId });
chat.startEventStreaming({ initialSinceId: null });

function ChatView() {
  const state = useSubscribableSnapshot(chat);
  return <MessagesList messages={state.messages} streaming={state.streamingRow} />;
}
```

## 2) VS Code extension (initial REST, later in-process)

### 2.1 Initial REST

```ts
import { FetchTransport, RestAgentBackend, SessionsController } from '@crystal-lattice/frontend-sdk';

const backend = new RestAgentBackend({ transport: new FetchTransport({ baseUrl }) });
const sessions = new SessionsController({ backend });
```

### 2.2 Later in-process

```ts
import { InProcessAgentBackend } from '@crystal-lattice/agent-runtime-node';

const backend = new InProcessAgentBackend({
  workspaceRoot,
  fs,
  secrets,
  logger,
});
```

The VS Code UI continues to use the same controllers and types.

## 3) Terminal (Python) adopting the same pattern

Even though terminal is Python today, the architecture mirrors the SDK approach:

- Terminal UI (prompt_toolkit) depends on a backend interface.
- Backends:
  - In-process (current): wraps `TerminalApplication` / `AgentApplication`
  - REST (new): calls the local/remote FastAPI server

This makes parity gaps obvious (if terminal works locally but not via HTTP, the missing server endpoints are clear).
