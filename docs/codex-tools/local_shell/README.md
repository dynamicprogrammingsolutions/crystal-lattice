# `local_shell`

`local_shell` is a special tool type exposed to the Responses API as `{ "type": "local_shell" }`.

Unlike `shell` / `shell_command`, it does not define a JSON schema in the request. It is implemented by Codex’s shell handler and uses the same output formatting and error conventions as other exec-like tools.
