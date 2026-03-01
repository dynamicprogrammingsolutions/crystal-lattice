# `request_user_input`

Prompts the human user with 1–3 short multiple-choice questions and waits for a response.

## Handler behavior (implementation notes)

- Availability is mode-gated: Codex only allows it in “Plan mode”.
- Each question must include non-empty `options`; otherwise the handler rejects the call.
- Codex forces `is_other=true` on each question so the client can always provide an “Other” freeform option.
- Tool output is a JSON-serialized response object (as a string).
