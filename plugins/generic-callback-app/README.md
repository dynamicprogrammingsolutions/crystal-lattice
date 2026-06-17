# Generic Callback App

Demo application plugin for testing generic external callback deep links.

The plugin exposes a `start_external_flow` action that builds a
`crystal-lattice://action/<connection>/<session>/<action>` callback URL and
returns it in a `copy_text` display action. The generated callback intentionally
omits the plugin id by default so tests can verify app-layer omitted-plugin
resolution.

It also exposes `complete_external_flow`, which echoes the callback inputs and
session context. This makes the plugin useful for SDK and mobile integration
tests without relying on a real OAuth or MCP provider.