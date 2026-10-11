# `write_stdin`

Pairs with `exec_command` to interact with a running unified exec session:
writes characters to the session (PTY sessions) or polls it for output.

## Handler behavior (implementation notes)

- Writes `chars` to the PTY of an existing session and returns “recent
  output”. Empty `chars` polls without writing.
- Non-empty writes are only supported for TTY sessions; writing to a
  pipe-backed session returns “stdin is closed for this session; rerun
  exec_command with tty=true to keep stdin open”. The exception is `\x03`,
  which interrupts the session (SIGINT semantics) on any session type.
- `yield_time_ms`: non-empty writes default to 250 ms and cap at 30000 ms;
  empty polls clamp to the 5000-300000 ms background range (default
  5000 ms).
- Output is truncated per call to `max_output_tokens` (default 10000).
- When the process finishes during a call, the response carries its
  `exit_code` and the session leaves the store; later calls report
  `Unknown process id <n>`.
- Unknown session ids return `Unknown process id <n>`.
