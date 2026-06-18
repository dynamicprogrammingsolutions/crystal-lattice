# `send_input`

Sends a message (or structured items) to a running sub-agent.

## Handler behavior (implementation notes)

- `interrupt=true` requests the target agent to stop current work and handle the new input immediately.
