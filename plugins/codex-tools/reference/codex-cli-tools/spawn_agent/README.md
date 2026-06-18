# `spawn_agent`

Spawns a sub-agent for a well-scoped task.

## Handler behavior (implementation notes)

- Returns an agent identifier that is then used with `send_input`, `wait`, `close_agent`, etc.
- Accepts either a legacy `message` string or structured `items`.
