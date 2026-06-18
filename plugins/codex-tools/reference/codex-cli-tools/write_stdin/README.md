# `write_stdin`

Pairs with `exec_command` to interact with a running session.

## Handler behavior (implementation notes)

- Writes `chars` to the PTY/pipes of an existing session and returns “recent output”.
- Output is truncated to `max_output_tokens` and also subject to the global truncation policy.
