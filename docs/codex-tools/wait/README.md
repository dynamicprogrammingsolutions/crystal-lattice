# `wait`

Waits for one or more agents to reach a terminal status.

## Handler behavior (implementation notes)

- Intended to avoid busy polling; the server will also emit notifications when agents complete.
