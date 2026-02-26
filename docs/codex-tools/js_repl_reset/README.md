# `js_repl_reset`

Restarts the js_repl kernel.

## Handler behavior (implementation notes)

- Clears persisted top-level bindings and resets the Node context.
- Returns a simple text acknowledgement.
