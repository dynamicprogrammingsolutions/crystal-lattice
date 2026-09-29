# Request-user-input tool with notification follow-up answers

Add a mid-turn user-question tool inspired by Codex upstream's
`request_user_input_async` / `send_user_message_async`, implemented with the
platform's session notifications and follow-up actions: the tool surfaces the
question as a notification, and the user's follow-up answer soft-cancels the
running request, waits for it to stop, appends the answer as a user message,
and starts a new request.

Background: the imported GPT-6 Sol/Luna system messages
(`instructions_default.20260922.md`) instruct the model to use
`functions.send_user_message_async` or `functions.request_user_input_async`
"depending on which is available". No such tool exists in this platform
today, so the instruction currently references a missing capability.

## Requirements checklist

- [ ] A first-party tool plugin exposes a request-user-input tool whose
  schema accepts one or more questions, each with a title and optional
  answer options, matching the upstream contract closely enough that models
  instructed by the GPT-6 templates can call it successfully.
- [ ] Calling the tool emits a session notification (through the tool
  `notification_sink`) that presents the question(s) and follow-up actions
  for answering: one action per option for single-option questions and a
  free-text answer path; the notification remains pending until answered or
  dismissed.
- [ ] The tool returns immediately with an acceptance result so the model
  can continue the turn; the tool call itself never blocks on the user.
- [ ] Submitting a follow-up answer executes an application action that:
  soft-cancels the request that was running when the question was asked (if
  it is still running), waits for that request to finish, then atomically
  appends the answer as a user message and starts a new request in the same
  session.
- [ ] The answer flow also works when the original request has already
  finished (no cancel/wait; append and resend only).
- [ ] The notification is resolved (or updated and resolved) when the answer
  is submitted, and stale follow-ups from an already-answered question do
  not send duplicate requests.
- [ ] The feature works over the public HTTP API and is usable from the
  mobile and desktop clients' existing notification rendering; the terminal
  at minimum reports the pending question without breaking.
- [ ] Unit and integration tests cover tool schema/execution, notification
  creation, the soft-cancel → wait → append → resend flow (including the
  already-finished race and the still-running timeout path), duplicate
  answer suppression, and end-to-end delivery through the public API.
- [ ] Plugin docs and the owning plugin README document the tool, the
  notification shape, and the answer flow.

## Requirement questions

1. **Tool naming.** Should the tool be registered under the exact upstream
   name `request_user_input_async` (and optionally also
   `send_user_message_async` as a thin alias), so models following the
   GPT-6 template text find it by name? Recommendation: yes — register
   `request_user_input_async` as the real tool and consider the alias only
   if testing shows models emitting the legacy name.
2. **Gating.** Register the tool for every agent that loads the plugin, or
   restrict it to agents whose model matches the GPT-6 family (mirroring
   upstream's `experimental_supported_tools` gating)? Recommendation: load
   per agent via config and let the model decide; the schema description
   already constrains use. No new model-gating machinery.
3. **Multi-question mapping.** For a call with several questions, render
   all questions in the notification body and provide a single
   "Answer questions" follow-up whose embedded form has one multiline field
   per question (options listed in the body), since follow-up forms have no
   select input today. Single-question calls with options get one action
   per option plus a free-text form action. Confirm this mapping is
   acceptable for v1.
4. **Wait timeout behavior.** If the soft-cancelled request does not finish
   within a bounded timeout (for example a long-running foreground tool),
   should the action report a retryable failure display and leave the
   notification pending, or block until completion? Recommendation:
   bounded timeout with a retryable failure display; hard cancel remains
   available to the user as today.

## Supporting details

### Upstream reference (openai/codex @ ea64727556, 2026-09-27)

- Handler: `codex-rs/core/src/tools/handlers/request_user_input_async.rs`.
  Schema: `questions: [{title: string, options?: string[]}]`, min 1
  question; options min 1 item, recommended answer first (first option is
  preselected upstream; free text always available).
- Semantics: emits a `TurnItem::AgentMessage` with
  `delivery: Async` + structured `questions`, returns
  `{"accepted":true}` immediately; the turn continues; the user's reply
  arrives as a new user message that steers the active turn.
- Naming history: `send_user_message_async` is a legacy catalog alias with
  no handler; `send_message_to_user_async` is a separate freeform-message
  tool (root sessions, exact catalog opt-in). Catalog
  `experimental_supported_tools` advertises `send_user_message_async` for
  gpt-6-astra/sol/luna only. GPT-5.6 and older neither advertise nor
  reference the tool.
- Gating upstream: root sessions only, `ToolExposure::DirectModelOnly`.
- Our templates: gpt-6-sol/gpt-6-luna `20260922` reference both names;
  gpt-6-astra `20260923` references `request_user_input_async` only;
  GPT-5.6 templates do not reference it.

### Platform building blocks (verified on develop @ 6322ca2a)

- Tool notification sink: `execute_tool` context key `notification_sink`;
  failure-contained session notification creation
  (`plugins/docs/notifications-and-action-displays.md`, "Tool notification
  sink").
- Follow-up actions: `run_action` follow-ups on notification displays with
  `fixed_params`; reference usage in
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_process.py`
  (`_cancel_followups` embeds `session_id` + `operation_id`).
- Embedded display forms: notification/action displays accept
  `form: {kind: "form", inputs: [...]}`; input types include `string` and
  `multiline`; no select type today. `run_action` follow-ups map submitted
  fields through `$form.<field_name>`
  (`plugins/docs/actions.md`, "Embedded display forms").
- Soft cancellation (task `20260927-hard-and-soft-request-cancellation`,
  shipped in ac972cab): `app.soft_cancel_request(request_id)` cancels the
  active provider call but lets a running foreground tool finish; the loop
  stops before the next phase; `request_cancelled` carries
  `cancellation_mode: "soft"`.
- Request identity: `app.get_active_session_request_id(session_id)`;
  `app.get_session_request_statuses(session_ids)` snapshot service.
- Atomic append+resend: `app.start_session_request_with_message(session_id,
  role=..., content=..., metadata=..., overrides=..., stream=True)` —
  returns `already_running` instead of starting; this is the resend entry
  point (HTTP: `POST /sessions/{session_id}/send_message`).
- Notification lifecycle: stable `key` reuse updates in place; resolve via
  `app.resolve_session_notification(session_id, notification_id, {...})`;
  `until_resolved` retention keeps the question answerable after the turn
  ends; revision conflict handling for stale dismissals already exists.
- Open gap: there is no public app-layer helper that *waits* for a request
  to finish; the action needs one (poll the status service or subscribe to
  request completion) — see plan step 3.

### Design sketch

```text
model ── tool call(request_user_input_async, questions)
         │ plugin validates, renders questions
         │ sink.create(session notification:
         │   body = questions, actions = option run_actions / answer form)
         ▼
       {"accepted": true}  ── model continues the turn
user ── taps option / submits form
         │ execute_action("answer_user_input")
         │   1. resolve notification (guards duplicates via revision/key)
         │   2. if original request still active:
         │        app.soft_cancel_request(request_id)
         │        wait for request completion (bounded timeout)
         │   3. app.start_session_request_with_message(
         │        session_id, role="user", content=<answer>)
         ▼
       new request streams; model sees the answer as the latest user message
```

Late answers (request already finished) skip step 2 and still work, which
matches the templates' "keep the question pending" guidance. Unanswered
questions simply stay pending and dismissible; the model proceeds with a
stated assumption exactly as its instructions describe.

## Execution plan

Status: Draft

### Step 1 — Plugin scaffold and tool

1. Create a new first-party plugin project (proposed
   `plugins/request-user-input-app`; final placement per question 2
   resolution) containing:
   - a `ToolPlugin` implementing `get_tool_schemas` (name per question 1,
     parameters mirroring the upstream `questions` schema with strict
     validation: non-empty titles, non-empty options) and `execute_tool`;
   - an `ApplicationPlugin` owning the `answer_user_input` action, its UI
     schema, and notification resolution.
2. `execute_tool` renders questions to markdown, creates the session
   notification through `context["notification_sink"]` with:
   - stable key `request_user_input:<request_id>` (per-question occurrence
     semantics follow the operation-occurrence guard pattern);
   - `display.presentation: "inline"`, `variant: "info"`, dismissible;
   - follow-up `run_action`s embedding `session_id`, `request_id`, and the
     option payload in `fixed_params` (compaction-plugin pattern);
   - retention `until_resolved`.
3. Tool result: `{"accepted": true}` immediately; the tool never blocks.

### Step 2 — Answer action: soft-cancel, wait, append, resend

1. `execute_action("answer_user_input", ...)`:
   - resolves the notification first (idempotent; a second submission for
     the same key must not resend — check resolution status before
     proceeding and return a friendly already-answered display);
   - if `app.get_active_session_request_id(session_id)` equals the stored
     `request_id`: `app.soft_cancel_request(request_id)`, then wait for
     completion using the new helper from step 3;
   - if no request is active (or a different one finished the session's
     turn): skip cancel/wait;
   - append the answer and resend via
     `app.start_session_request_with_message(...)`; on
     `already_running` (race with another submission) wait once more and
     retry, then surface a retryable failure display.
2. Answer content: chosen option text, or the composed form answers
   (one line per question for multi-question forms), sent as a normal user
   message so it lands in provider history like any steering message.

### Step 3 — App-layer wait helper

1. Add a small public `AgentApplication` helper (name along the lines of
   `wait_for_request_completion(request_id, timeout)`) implemented over
   the existing session-request status service (poll or completion event),
   with a bounded default timeout per question 4.
2. Cover it with focused application-layer tests, including timeout and
   unknown-request-id behavior.

### Step 4 — Surfaces and wiring

1. HTTP: no new routes required (notifications, actions, and
   `send_message` already exist); verify follow-up action execution over
   the public API in an integration test.
2. Mobile/desktop: rely on existing session-notification rendering and
   embedded forms; verify option actions and the answer form render and
   submit; fix only defects found.
3. Terminal: ensure pending-question notifications print the question
   (event rendering) even if follow-up actions are not interactive there;
   the composer remains a manual answer path.
4. Config wiring: add the plugin to the default configuration for agents
   using Codex-style developer messages (default config + documented
   personal-config step), respecting question 2.

### Step 5 — Tests and docs

1. Unit: schema validation, notification payload shape, action logic
   (duplicate suppression, already-finished path, timeout path) with a
   fake app.
2. Integration: full flow through the HTTP API with a recording provider —
   tool call during a running request, follow-up submission, observed soft
   cancellation (`cancellation_mode: "soft"`), appended user message, and
   the resent request containing the answer; plus the late-answer variant.
3. Docs: plugin README + `plugins/docs/` cross-links (tool plugins,
   notifications/actions), and a note in the agent-creation development
   page that GPT-6 templates reference this tool.

### Implementation decisions and open questions

The four requirement questions above (naming, gating, multi-question
mapping, wait timeout) need answers before execution; recommendations are
included with each. Local reversible choices proposed in the plan: new
plugin project under `plugins/`; notification key scheme
`request_user_input:<request_id>`; `until_resolved` retention.

### Documentation

- New plugin README (authoring, schema, notification shape, answer flow).
- `plugins/docs/tool-plugins.md` and
  `plugins/docs/notifications-and-action-displays.md` cross-references.
- `application/python/docs/development/agent-creation.md`: note that the
  GPT-6 instruction assets reference the tool and how to enable it.

### Task checklist

- [ ] Resolve requirement questions 1–4
- [ ] Step 1: plugin scaffold, tool schema/execution, notification creation
- [ ] Step 2: answer action with cancel/wait/append/resend
- [ ] Step 3: app-layer wait helper + tests
- [ ] Step 4: HTTP/mobile/desktop/terminal verification, config wiring
- [ ] Step 5: unit + integration tests, docs

### Requirement verification

| Requirement | Acceptance evidence |
|---|---|
| Tool schema + immediate return | Unit tests on schema/validation; tool returns `accepted` without blocking |
| Notification with follow-ups | Unit test asserting notification record shape (body, actions, retention) via a captured sink |
| Answer flow (running request) | HTTP integration test with recording provider: soft cancel observed, wait, user message appended, new request contains the answer |
| Answer flow (already finished) | Integration variant with no active request: append + resend only |
| Duplicate suppression | Unit test: second submission after resolution does not resend |
| Client surfaces | Mobile/desktop notification + form rendering exercised through existing SDK paths; terminal prints the question |
| Docs | Plugin README and docs pages updated |

### Additional implementation verification

- `pytest plugins/<new-plugin>/tests -q`
- `pytest application/python/tests -q` (wait helper + server integration)
- Focused mobile/desktop package tests touched by rendering fixes, if any
- `ruff check` + `black` on new/changed files; `pyright` with no new errors

### Risks

- The wait helper must not deadlock the application event loop; implement
  over the existing status service with a background-safe wait.
- Follow-up form capabilities differ per client; verify the free-text path
  on both mobile and desktop before committing to the form mapping.
- Models may call the tool when no request-sending loop is active (for
  example during finalize); the action's already-finished path covers the
  common case, and unknown request IDs must fail softly.