# Embedded iOS configuration

The iOS in-process runtime uses a maintained application configuration at:

```text
application/python/agent_terminal_app/default_config/embedded-ios/config.json
```

This file owns the embedded providers, agents, plugin catalog, tool-family
assignments, application plugins, mixins, and fixed Reviewer deployment
settings. The mobile application does not construct a parallel agent graph.

The iOS preparation script copies the configuration into
`crystal_lattice_app.zip` under the same `agent_terminal_app` package path.
At runtime, the embedded adapter copies the raw JSON unchanged into the app's
Application Support config directory and creates `AgentApplication` with a
config-only placeholder environment. Placeholder values do not need to be
installed in process-global `os.environ`.

## Placeholder ownership

The native settings bridge owns persisted user choices and supplies values for
these categories:

- workspace and application-data paths;
- provider enabled/readiness state;
- editable provider URLs and model ids;
- OpenAI API versus ChatGPT mode;
- API keys loaded from Keychain;
- ChatGPT credential and rate-limit paths;
- the bundled Reviewer CA path;
- cost-tracking storage.

The Reviewer URL, model, provider, protocol, and tool family are literals in
the maintained JSON. The app exposes only a global Reviewer visibility toggle
and its caller API key.

The maintained and app-support JSON remain secret-free. API keys are resolved
from the config-only placeholder map in memory. ChatGPT credentials remain in
their plugin-owned file under the app-support auth directory.

## Agent availability

The JSON contains the complete supported topology. Agent entries use an
`enabled` placeholder. `AgentApplication` filters false-like agent values
(`false`, `0`, `no`, `off`, or an empty value) while loading configuration and
does not forward the control key into provider configuration.

This keeps topology reviewable while allowing native settings to make
incomplete profiles unavailable. Reviewer availability additionally requires
the global Reviewer toggle.

## Default-plugin parity

The embedded runtime includes these ordinary default-config capabilities:

| Capability | Embedded status |
| --- | --- |
| System message | Included |
| Request options | Included |
| Timestamp and duration | Included |
| ChatGPT authentication | Included |
| Session actions, title, search, status, pinning, archive, ordering, metadata, and attachments | Included |
| Summarize range | Included |
| Rebuild native history | Included |
| Cost tracking | Included |
| Per-session working directory | Included; existing descendants of the fixed app workspace |
| OpenAI Responses native web search | Included for direct OpenAI and Reviewer |
| OpenRouter native web search | Included |
| OpenAI Responses image attachments | Included in inline-image mode; Files API/PDF upload is unavailable on the requests transport |
| OpenRouter image attachments | Included |
| OpenAI Flex, Fast mode, prompt caching, and verbosity | Included where the provider/model and API authentication mode support them |
| OpenAI native compaction | Excluded; it imports the OpenAI SDK, which is outside the requests-only iOS dependency set |
| File context | Deferred; GitPython dependency and mobile file-context UX require review |
| Provider-neutral Tavily search | Deferred; native search currently covers only OpenAI Responses and OpenRouter |
| Web context | Deferred; trafilatura dependency overlaps later Tavily work |
| MCP runtime | Deferred until an embedded MCP runtime is approved |
| Cloud agent | Excluded from the on-device runtime |
| Application-config dotenv editing | Excluded; native settings and Keychain own embedded credentials |

The OpenAI Responses provider receives an explicit empty
`auth_mode_options` list. That hides the ordinary session API/ChatGPT selector
for embedded agents, leaving the global on-device settings as the sole auth
control. Other OpenAI Responses consumers retain the ordinary selector.

Flex and Fast service-tier controls are hidden when the embedded OpenAI
profile uses ChatGPT authentication. They are also hidden for Reviewer so its
fixed proxy pricing and daily budget cannot be changed by a session control.

## Workspace and working directory

`workspace_root` is the fixed app-owned filesystem authorization boundary.
`working_directory` is the session-specific directory used to resolve
relative file-tool paths. The embedded workspace package contributes a
`workspace` control whose value is an opaque `workspace_id`, plus
plugin-driven action buttons for creating private/shared workspaces and
selecting a folder from iOS Files.

Known choices are classified as:

- private directories under the current session's app-owned area;
- shared directories under the fixed app workspace; and
- native-host-authorized external directories represented by opaque grant
  IDs.

The native host stores and restores security-scoped bookmarks and injects only
active grant IDs, display names, and resolved authorized roots into the
embedded runtime. Session metadata stores `workspace_id` and the canonical
effective `working_directory`, never a bookmark. Direct path updates remain
limited to the app workspace; an external path is accepted only when derived
from an active registered grant.

Both Claude-like and Codex-like tools use the selected working directory as
their immediate root. The shared resolver accepts the fixed app root plus
active external grants as authorization boundaries, while still rejecting
parent traversal, sibling access, symlink escape, missing directories, and
unregistered external paths.

## Verification

Relevant boundaries include:

```bash
pytest application/python/tests/test_embedded_ios_default_config.py -q
pytest mobile/crystal-lattice-control-rn/python_tests -q
npm run build:ios:embedded-providers:bundle
npm run test:ios:embedded-providers:bundle
npm --prefix mobile/crystal-lattice-control-rn run detox:build:ios
```

Archive verification must confirm that the configuration and included plugin
packages are imported from `crystal_lattice_app.zip`, without repository or
development-dependency fallback.