# Generic Callback App

Demo application plugin for testing generic external callback deep links.

The plugin exposes a `start_external_flow` action that builds a
`crystal-lattice://action/<connection>/<session>/<callback-element>` URL and
returns it in `open_url` and `copy_text` display actions. The generated callback intentionally
omits the plugin id by default so tests can verify app-layer omitted-plugin
resolution against one applicable `session_action_callback`.

It binds `complete_external_flow` through the
`generic_callback_complete_external_flow` callback UI element. The procedure
echoes the explicitly mapped callback inputs and session context, making the
plugin useful for SDK and mobile integration tests without relying on a real
OAuth or MCP provider. A bare `complete_external_flow` action id is not a
deep-link target.