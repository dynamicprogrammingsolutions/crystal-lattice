# Plugin-Driven CLI And Interactive Terminal Commands

Expose application-plugin actions through action-backed command UI elements,
an applicable-element `/action` launcher, shared terminal result rendering,
and automatic application/current-session notification presentation without
introducing a second execution API.

## Requirements checklist

### Action and command model

- [x] Application actions remain callable procedures and do not become
  commands merely because they exist.
- [x] Only applicable action-backed UI elements expose actions through
  top-level CLI commands, interactive slash commands, `/action`, direct-result
  follow-ups, or notification follow-ups.
- [x] `cli_command` and `slash_command` are separate UI element types that may
  bind the same action while defining frontend-appropriate names, aliases,
  argument presentation, and scope.
- [x] Legacy `ApplicationPlugin.get_commands()` contributions remain
  top-level CLI compatibility bindings only and never create slash commands or
  `/action` entries.
- [x] The interactive terminal discovers applicable contributed slash
  commands after application configuration and plugin loading and refreshes
  them after application replacement.
- [x] Dynamic terminal help and completion include applicable contributed
  command names, descriptions, aliases, and supported arguments.
- [x] Command-name and alias collisions are detected and reported
  deterministically before an action is invoked.

### `/action` UX

- [x] `/action` lists and executes only applicable action-oriented UI elements
  for the application and active session; it never enumerates bare action
  definitions.
- [x] `/action --message INDEX` uses the same canonical message indexes and
  normalization as `/list INDEX` and exposes only message actions applicable
  to that selected message.
- [x] `/action` identifies elements by UI element id plus plugin and scope
  qualification when needed, and listing prints a canonical executable command
  for every enabled entry.
- [x] Action forms preserve the UI-defined input order and support inline
  `name=value` prefill, context prefill, defaults, required prompts, optional
  skips, and `submit_empty`.
- [x] Terminal forms support text, integer, number, select/dropdown, boolean,
  multiline, secret, and password input with type-appropriate prompting,
  coercion, validation, and safe display.
- [x] Confirm and form cancellation returns to the prompt without invoking the
  bound action or mutating session, credential, or plugin state.
- [x] Disabled action UI elements remain visible with a reason and cannot be
  invoked.
- [x] Application-, session-, session-list-, and message-scoped elements
  receive only their valid context, fixed parameters, and mapped parameters.
- [x] Bound action definitions perform final validation for command arguments,
  inline values, prompted values, defaults, and mapped context.

### Results and follow-ups

- [x] Top-level commands, slash commands, `/action`, direct action results,
  foreground progress, and notifications use one terminal result renderer for
  displays, errors, variants, follow-up information, and UI effects that have
  terminal meaning.
- [x] Every valid direct-result `run_action` follow-up is registered as an
  executable terminal command reference when rendered, and the renderer prints
  the exact command needed to invoke it later.
- [x] Direct-result follow-up execution preserves the existing `fixed_params`,
  `param_map`, embedded `form`, follow-up `dialog`, session endpoint selection,
  and `preserve_display` contracts.
- [x] Non-executable follow-ups such as `open_url`, `copy_text`, download, and
  dismiss remain visibly represented without inventing provider-specific
  terminal behavior.

### Notifications

- [x] Pending application notifications and pending notifications for the
  active session render automatically when received; notifications belonging
  to inactive sessions are ignored.
- [x] The terminal hydrates authoritative application and active-session
  notifications at startup, after application replacement, after an applicable
  event-stream reconnect/cursor recovery, and whenever the active session
  changes.
- [x] Notification presentation deduplicates identical observations and
  supersedes older content and follow-up registrations by notification
  identity and revision.
- [x] Valid notification `run_action` follow-ups are registered immediately,
  and notification rendering prints the exact terminal command reference.
- [x] Before invoking a notification follow-up, the terminal rereads the
  authoritative notification, requires the current pending revision and
  follow-up to remain valid, and executes the current registered action
  binding rather than stale rendered parameters.
- [x] Terminal notification UX is automatic and event-driven with
  authoritative hydration; no notification listing command or pull-only user
  workflow is added.

### Foreground authentication workflows

- [x] Authentication plugins can contribute one complete foreground login
  command that starts the provider flow, presents authorization instructions,
  reports progress, waits for a terminal outcome, and returns only after
  success, failure, cancellation, or expiry.
- [x] A contributed command can remain active while provider-owned background
  work or an attempt-scoped callback listener runs without moving protocol
  logic into the terminal.
- [x] Terminal interruption can request provider-owned, attempt-scoped
  cancellation and return control without allowing stale completion to replace
  newer command, login, or credential state.
- [x] Authentication plugins may contribute separate management intents such
  as logout, but normal login never requires users to coordinate separate
  start, status, and cancel commands.

### Safety and compatibility

- [x] Plugin actions remain the single executable source of truth for every
  command, `/action` entry, and `run_action` follow-up.
- [x] Invalid, inapplicable, disabled, stale, or ambiguous entries fail before
  action invocation.
- [x] Sensitive values are excluded from help, completion, command echoes,
  notification/result rendering, logs, and ordinary diagnostics.
- [x] Existing static terminal commands and legacy top-level contributed
  commands remain compatible during migration.
- [x] Automated tests prove that every supported entrypoint invokes its bound
  plugin action and the same validation, parameter-mapping, and result
  contracts.

## Scope

This task owns:

- the `cli_command` and `slash_command` action-backed UI element contracts;
- compatibility adaptation for legacy `get_commands()` declarations;
- dynamic top-level and interactive command discovery;
- the generic `/action` terminal launcher for applicable action UI elements;
- shared action/result/follow-up rendering and terminal-local executable
  references;
- automatic application and active-session notification presentation,
  hydration, revision handling, and notification follow-up registration;
- one deterministic ChatGPT device-code command consumer proving the generic
  foreground workflow.

Provider-specific command elements remain in their owning plugins.
Provider-owned polling, callback listeners, protocol exchange, credential
persistence, and attempt state remain outside the terminal.

Out of scope:

- Codex browser OAuth and redirect-mode support;
- Anthropic or other provider adoption;
- mobile/desktop command frontends;
- global attention indicators, cross-session notification aggregation, focus
  changes, badges, sounds, or a notification center;
- user-facing notification listing commands or a pull-only notification UX;
- changing notification storage, retention, dismissal, or event contracts
  beyond the terminal consumer behavior needed here.

This task supersedes:

- `tasks/20260605-mobile-oauth-login-flows/030-cli-login-commands-via-plugin-actions.md`
- `tasks/20260315-terminal-action-command.md`

## Resolved requirement decisions

The user approved all six recommended resolutions on 2026-10-02.

1. What exact route and alias fields should `cli_command` and `slash_command`
   use?
   - Recommendation: `cli_command` carries a token `path` and optional
     full-path `aliases`; `slash_command` carries a slash-free token `path`
     and optional full-path aliases. Both reuse the ordinary action element's
     `action_id`, `action_owner`, `fixed_params`, `param_map`, `dialog`,
     `condition`, `disabled`, `disabled_reason`, and `scope`.
   - Recommendation: no collision has precedence. Canonical paths and aliases
     collide within their frontend namespace, including against built-ins,
     and all conflicting owners are reported in stable path/plugin/element
     order.
2. What generic UI metadata should describe a foreground command workflow?
   - Recommendation: a command element statically declares existing start,
     status, and cancel action bindings; attempt-id mappings; a state path;
     pending/success/failure/cancelled/expired values; and bounded poll timing.
     Every step remains an ordinary action invocation.
   - Alternative: dynamic continuation action references in results are more
     flexible but cannot be fully validated before the start action mutates
     provider state.
3. The first consumer uses `crystal-lattice auth login codex` and
   `/login codex`, with no implicit provider inference and no method argument
   for the current device-only flow. Logout is deferred as a separate intent.
4. What exact interruption outcome should the standalone CLI guarantee?
   - Recommendation: both frontends invoke the attempt-scoped cancel action
     once and wait for bounded cleanup. The interactive terminal restores the
     prompt; standalone CLI exits 130. Cancellation failure is rendered safely
     but does not trap the user in the foreground command.
5. What browser-opening capability belongs in the generic command contract?
   - Recommendation: always print a copyable/clickable URL. Allow best-effort
     automatic opening only when a provider-declared browser flow runs in a
     local interactive frontend, with an explicit no-open option. Device-code,
     remote, and headless flows never auto-open.
6. How long should terminal-local direct-result command references remain
   valid?
   - Recommendation: a direct reference remains executable until its source
     `display_id` is superseded, `preserve_display: false` removes it after a
     follow-up starts, application replacement makes its binding invalid, or
     the terminal exits. Notification references instead follow authoritative
     notification identity/revision and are never executed from a stale
     snapshot.

## Supporting facts

### Current command and action behavior

- `ApplicationPlugin.get_commands()` and
  `AgentApplication.get_application_commands()` expose opaque compatibility
  dictionaries. The only first-party non-empty contribution is
  `cloud-agent-app`'s top-level `validate-cloud`.
- The top-level entrypoint executes a legacy command through
  `execute_application_action(...)`, but duplicate names currently collapse
  through a last-wins dictionary and nested paths/aliases are unsupported.
- The interactive terminal has a process-global static decorator registry.
  It does not consume application UI elements and can retain no
  application-generation-specific command state.
- `AgentApplication.execute_action_with_metadata(...)` already resolves
  application and current-session action owners, validates action inputs, and
  enriches application-action context from a session id. It remains the one
  execution boundary.
- Application and session UI schema already carry applicable action bindings.
  Session application UI is generated with the current session's effective
  config, tags, models, serialized session, and session id. UI `condition`
  supports contextual visibility.

### Current action form and result contracts

- Ordinary action UI elements bind `action_id` and optional `action_owner`,
  `fixed_params`, `param_map`, `dialog`, `condition`, and finite `order`.
  Fixed parameters are applied first; successfully resolved mappings replace
  them; missing mappings submit nothing; the action definition applies
  defaults and final validation.
- Form inputs are ordered and support `name`, `type`, `label`, `description`,
  `placeholder`, `default`, `required`, `options`, `prefill_from`, and
  `submit_empty`. Context prefill wins over defaults when usable. Secret and
  password fields are never prefilled.
- Message actions map `$message.index` and message fields. `/list` already
  displays canonical zero-based message indexes and resolves negative input to
  one concrete stored index through `TerminalApplication.show_message(...)`.
- Successful action results may return `display` with title/body/variant,
  embedded `form`, and follow-ups. Supported follow-up kinds are
  `run_action`, `open_url`, `copy_text`, `download_attachment_asset`, and
  `dismiss`.
- A direct `run_action` follow-up already has plugin/action identity, optional
  owner, fixed parameters, parameter mappings, optional dialog, and
  `preserve_display`. The frontend SDK converts it to a synthetic
  `action_result_followup` action element and retains the originating display
  form for `$form.*` mappings. The terminal should consume this contract, not
  invent another follow-up action shape.

### Current notification contracts

- Application notifications are durable in the injected notification store;
  session notifications are persisted in
  `Session.metadata["notifications"]["items"]`.
- Notifications have stable `id`, stable-key occurrence behavior, monotonic
  positive `revision` (with `updated_at` legacy fallback), and pending,
  dismissed, resolved, or expired status. Active list calls return pending
  records.
- Repeated publication of the same active key updates that notification and
  increments its revision. Operation ids prevent late updates from a
  superseded in-progress operation occurrence.
- Application notification events are global and carry no session id. Session
  notification events carry their owning session id. Events are best effort;
  authoritative list/session state is the reconnect authority.
- The terminal currently polls events filtered to the active session. It
  therefore does not receive global application notification events and has no
  notification hydration, revision merge, rendering, or follow-up registry.
- Existing frontend logic merges events by notification id and accepts only a
  newer revision/timestamp. Notification mutations accepting
  `expected_revision` reject stale gestures.

### Reference foreground-login review

The comparison was made against locally available source revisions:

- `pi` at `e44d75c20` uses provider-owned async login interactions,
  structured URL/device/progress events, prompts, an abort signal, loopback
  callback/manual-input racing, and listener cleanup in `finally`.
- OpenCode at `1c7c03332` returns URL/instructions plus an async automatic or
  code-input callback, then prints progress and awaits one foreground result.
- Codex at `0650d6d1ca` prints a fallback URL, offers browser/device methods,
  tracks login ids, forwards cancellation, restores terminal state, and
  ignores stale completion notifications.

## Execution plan

Status: Approved

After the remaining questions are approved, make UI schema the sole
presentation/discovery source and keep action definitions as callable
procedures. The terminal will adapt applicable action-backed UI elements into
command routes, `/action` entries, result follow-up references, and automatic
notification presentation while executing only through
`execute_action_with_metadata(...)`.

### UI element ownership and command discovery

1. Add normalized `cli_command` and `slash_command` action UI element
   contracts alongside existing application/session/message action elements.
   Validate element identity, route/aliases, action binding, scope, mappings,
   dialog/form metadata, disabled metadata, foreground metadata, and sensitive
   fields. Cross-check every element against an existing action definition
   without making that definition discoverable by itself.
2. Treat applicability as a UI-schema decision: the element must be returned
   for the relevant application/session configuration, pass its contextual
   `condition`, and have the context required by its declared scope. A
   `disabled` element remains listable with `disabled_reason` (falling back to
   `description`) but is not executable.
3. Adapt each valid legacy `get_commands()` entry into an internal
   compatibility `cli_command` only. Preserve `validate-cloud` behavior and
   help. Never expose that adapter to slash discovery or `/action`.
4. Build an immutable frontend command view per `AgentApplication`
   generation. Resolve slash commands from the current
   `TerminalApplication`, merge with static built-ins for help/completion, and
   never mutate the module-global static registry. Rebuild on owner
   replacement so unloaded plugins leave no stale route.
5. Validate canonical routes and aliases against plugin contributions and
   built-ins before invocation. Report deterministic conflicts and do not
   choose a winner.

### Concrete `/action` UX and invocation

Use this grammar:

```text
/action
/action [--scope application|session|session-list] [--plugin PLUGIN] ELEMENT_ID [NAME=VALUE ...]
/action --message INDEX
/action --message INDEX [--plugin PLUGIN] ELEMENT_ID [NAME=VALUE ...]
/action --ref REFERENCE
```

- `/action` lists applicable `application_action`, `session_action`, and
  `session_list_action` elements for the active application/session. It does
  not list `cli_command`, `slash_command`, lifecycle-only definitions, or bare
  actions.
- `/action --message INDEX` calls the same message resolver as `/list INDEX`,
  normalizes negative input to the canonical non-negative stored index, loads
  that exact message, evaluates message conditions, and lists only applicable
  `message_action` elements.
- Entries are ordered by finite UI `order`, with missing order after ordered
  entries and declaration order as the stable tie-breaker. Each line includes
  label, plugin, scope, description, enabled/disabled state, disabled reason,
  and the fully qualified canonical invocation.
- A unique element id may be invoked without qualification. Ambiguous ids
  require the listed `--plugin` and, when application/session/session-list
  scopes still collide, `--scope`. Message scope is selected only through
  `--message`.
- `application_action` receives application context only. `session_action`
  receives the active session and effective config. `session_list_action`
  maps against the active session's authoritative summary.
  `message_action` additionally receives the selected canonical index and
  serialized message. Missing required scope/context rejects before action
  invocation.
- Fixed parameters are applied first. Context mappings are resolved next.
  Inline `NAME=VALUE` values prefill only declared form inputs and take
  precedence over `prefill_from`, which takes precedence over `default`.
  Unknown inline names fail before prompting. Secret/password values are
  rejected inline so they cannot enter terminal history.
- `dialog.kind: none` executes after preflight. `confirm` prints title/message
  and requires an explicit yes; no, Escape, or Ctrl-C cancels without calling
  the action. `form` prompts in exact `inputs` order.
- Required fields reprompt until a syntactically valid value is supplied or
  the form is cancelled. Optional fields show their default/prefill when safe;
  Enter accepts that value. Enter with no value skips an optional field that
  has no initial value, and the reserved prompt response `:skip` explicitly
  skips an optional default/prefill. `submit_empty` replaces skip behavior with
  submission of an explicit empty string.
- Text is submitted as a string. Integer and number inputs parse before
  invocation. Select/dropdown inputs show ordered labels and submit the
  selected option value. Boolean/checkbox inputs accept explicit
  true/false/yes/no choices. Multiline input uses a multiline prompt with
  Ctrl-D to submit and Ctrl-C/Escape to cancel. Secret/password input is
  masked, never prefilled or echoed, and held only for the invocation.
- After mapping and prompt coercion, the bound action definition performs
  final defaulting and validation. Any mapping, prompt, type, disabled,
  applicability, or ambiguity error occurs before the action call.

### Shared result rendering and command references

1. Introduce one terminal renderer for direct action results, contributed
   commands, `/action`, foreground status, and notifications. It renders
   standard title/body/variant/presentation hints, safe errors, meaningful UI
   effects, and every follow-up label.
2. Convert each valid direct-result `run_action` follow-up through the same
   synthetic `action_result_followup` shape used by the frontend SDK. Register
   an opaque terminal-local reference and print its exact invocation, for
   example `/action --ref result-1`.
3. On reference invocation, prompt the originating embedded display `form`
   first and any follow-up `dialog` second, preserving their separate `$form`
   and `$dialog` mappings, field order, fixed parameters, action owner, source
   session/message context, endpoint selection, and final action validation.
4. Retain or retire a direct reference according to the approved lifetime and
   `preserve_display` decision. Revalidate the referenced action against the
   current application generation before execution.
5. Render `open_url` as a copyable/clickable URL, `copy_text` as clearly
   delimited text, download metadata as an unsupported-or-available terminal
   instruction, and dismiss as local presentation behavior where meaningful.
   Do not auto-execute any follow-up.

### Automatic notification presentation

1. Add a terminal notification observer with an application-scope event cursor
   in addition to existing active-session request polling. It accepts
   application notification events and session notification events only for
   the current session; it discards inactive-session events without rendering
   or registering follow-ups.
2. Hydrate active authoritative application notifications and active
   current-session notifications using snapshot/list APIs with terminal
   history excluded:
   - at terminal startup after the initial active session exists;
   - after `AgentApplicationOwner` replacement;
   - after cursor expiry or other applicable event-stream reconnect;
   - after new-session creation or current-session switch.
   Capture the global event cursor before hydration and resume from that cursor
   so snapshot/event races converge through revision deduplication.
3. Use `(scope, session_id when scoped, notification_id)` as identity and
   revision (or legacy `updated_at`) as version. The same version renders once.
   A newer pending version supersedes displayed content and registrations.
   Dismissed/resolved/expired versions retire registrations and do not replay
   pending presentation.
4. Render every newly accepted pending application or active-session
   notification immediately through the shared renderer. Do not navigate,
   focus another session, aggregate inactive sessions, play sounds, set badges,
   or create a notification center.
5. Validate each notification `run_action` follow-up and register a stable
   notification reference immediately, printing an exact command such as
   `/action --ref notification-1`. A newer revision updates or removes that
   logical reference according to the current follow-up id.
6. Before notification-reference execution, reread the authoritative
   application or active-session notification. Require it to remain pending,
   compare its current revision, locate the same follow-up id, rebuild the
   synthetic action element from that current revision, and revalidate its
   action/context. If the record is terminal, missing, moved to an inactive
   session, or no longer contains the follow-up, fail before action invocation.
7. Do not add `/notifications`, `/notification list`, or any equivalent pull
   command. Internal hydration is recovery, not the user presentation model.

### Foreground workflow and first consumer

- Add the approved foreground metadata to command UI elements and validate all
  start/status/cancel bindings and mappings before the start action.
- Execute the start action once, render it, poll the declared status action
  while pending, and stop only on a declared terminal state. Every step uses
  ordinary action dispatch.
- Carry the returned attempt id into status and cancellation actions. Reject
  continuation results for another attempt. Make ChatGPT auth worker writes,
  status, and cancellation attempt-scoped so an older worker cannot replace a
  newer attempt or credentials.
- Add a terminal foreground controller that forwards one interruption,
  performs bounded provider cleanup, and restores prompt/signal/completion
  state. Keep all provider names, OAuth endpoints, callback servers, and token
  logic out of generic terminal modules.
- Add applicable `cli_command` and `slash_command` elements to
  `chatgpt-auth-app` for the approved complete device-code flow. Keep its
  ordinary start/status/cancel actions and action UI available to other
  frontends.

### Sensitive data and compatibility

- Mark sensitive form fields from `secret`/`password` metadata. Redact exact
  values known to an invocation in addition to sensitive-key heuristics.
  Never include them in completion, help, canonical commands, prompt logs,
  exceptions, result rendering, or notification command references.
- Preserve all current static slash commands, `/help`, feature completions,
  canonical `/list` indexing, action mapping/default behavior, and legacy
  top-level contributed command parsing.
- Keep returned UI/action/notification structures immutable by convention and
  avoid terminal-global mutable registries tied to an application generation.

### Implementation decisions and open questions

- Approved: actions are callable procedures; only applicable action-backed UI
  elements expose them.
- Approved: `cli_command` and `slash_command` are separate UI element types and
  may bind the same action.
- Approved: legacy `get_commands()` is top-level CLI compatibility only and
  never creates slash commands.
- Approved: `/action` exposes only applicable action-oriented UI elements, not
  action definitions or command elements.
- Approved: application and active-session notifications present
  automatically with authoritative hydration and identity/revision
  supersession; inactive-session notifications are ignored.
- Approved: notification listing commands, pull-only UX, global attention,
  cross-session aggregation, focus changes, badges, sounds, and a notification
  center are excluded.
- Approved: use the concrete `/action` grammar, ordered form behavior, opaque
  `--ref` commands, disabled-reason field, and notification reference
  revalidation described above.
- Approved: use token paths/full-path aliases with no collision winner; static
  foreground metadata; `codex` spelling without a device-flow method argument
  and with logout deferred; bounded cancellation with interactive restoration
  and standalone exit 130; the recommended browser-opening policy; and the
  recommended direct-result reference lifetime.

### Documentation

- Update `plugins/docs/ui-elements.md` with `cli_command` and `slash_command`,
  scope, route/alias, disabled-reason, dialog/form, applicability, collision,
  foreground, and legacy-adaptation rules.
- Update `plugins/docs/application-plugins.md` to state that actions are
  procedures and UI elements are the only exposure mechanism.
- Update `plugins/docs/actions.md` for terminal consumption of direct
  `run_action` follow-ups, form/dialog mapping, registered references, and
  shared rendering.
- Update `plugins/docs/notifications-and-action-displays.md` with automatic
  terminal delivery, hydration points, active-session filtering,
  identity/revision deduplication, authoritative follow-up invocation, and the
  explicit terminal exclusions.
- Update `application/python/docs/terminal.md` with dynamic commands, the exact
  `/action` grammar, canonical message-index usage, ordered prompts, disabled
  reasons, cancellation, reference commands, and automatic notifications.
- Update
  `application/python/docs/development/terminal-and-http-features.md` with
  generation ownership, dual event cursors, hydration race handling,
  reference-registry lifetime, and production-path test seams.
- Update `plugins/chatgpt-auth-app/README.md` for the one-command device-code
  flow while preserving action-based non-terminal usage.
- Update `validate-cloud` documentation only if compatibility help text
  changes. Do not document excluded notification-center or provider-browser
  behavior as current.

### Task checklist

- [x] Verify the required repository working directory and git top level.
- [x] Inspect and record current direct-result `run_action`, ordered
  dialog/form, parameter mapping, message-index, notification storage/event,
  hydration, identity, and revision contracts.
- [x] Inspect and record the current local `pi`, OpenCode, and Codex login
  behavior and source revisions.
- [x] Obtain approval for remaining open questions 1–6 and record the exact
  Codex/device-flow/logout resolution.
- [x] Add and normalize action-backed `cli_command` and `slash_command` UI
  element contracts and deterministic collision validation.
- [x] Adapt legacy `get_commands()` entries to compatibility CLI elements only.
- [x] Add generation-scoped top-level/slash discovery, help, completion, and
  reload invalidation without changing the static registry.
- [x] Implement the specified applicable-element `/action` listing,
  qualification, message context, ordered forms, prompting, cancellation,
  disabled handling, mapping, and execution.
- [x] Add shared result/notification rendering and terminal-local direct
  `run_action` references.
- [x] Add automatic application/current-session notification event delivery,
  authoritative hydration, revision supersession, and inactive-session
  filtering.
- [x] Add authoritative notification follow-up registration and invocation.
- [x] Add approved foreground workflow polling, interruption, cleanup, and
  stale-attempt protection.
- [x] Contribute the approved ChatGPT device-code command UI elements and
  deterministic local tests.
- [x] Add secret-aware prompting and diagnostic redaction.
- [x] Update plugin-author, action, notification, terminal-user,
  terminal-development, ChatGPT, and conditional compatibility documentation.
- [x] Run focused and package-level verification and record requirement
  evidence before marking requirements complete.

### Requirement verification

- UI exposure and shared action execution — Verified by
  `test_public_cli_resolves_nested_command_path`,
  `test_dynamic_slash_and_action_use_same_action_and_ordered_form`, and
  `test_action_inventory_excludes_bare_procedures_and_orders_ui_elements`.
  The public CLI subprocess, production slash dispatcher, and `/action`
  dispatcher reach the same fixture action; its unexposed bare procedure is
  absent from inventory and resolution.
- Legacy isolation and collisions — Verified by
  `test_get_application_actions_and_ui_schema_attach_plugin_id`,
  `test_command_catalog_separates_frontends_and_reports_collisions`, the
  54-test cloud package run, and
  `test_validate_cloud_public_help_remains_compatible`. Legacy commands are
  CLI-only, and exact, alias, built-in, and built-in-prefix collisions fail
  deterministically.
- `/action` application/session behavior — Verified by
  `test_action_inventory_excludes_bare_procedures_and_orders_ui_elements`,
  `test_action_cancellation_and_disabled_reason_prevent_invocation`, and
  `test_application_session_and_session_list_scopes_map_only_valid_context`.
  These exercise ordering, disabled reasons, applicability, qualification,
  application context isolation, session context, and authoritative
  session-summary mapping.
- Message behavior — Verified by
  `test_message_action_uses_list_index_and_condition` and
  `test_direct_followup_preserves_message_context_and_nonpreserving_lifetime`.
  Negative input resolves to canonical index zero, conditions exclude the
  assistant message, and follow-ups retain the selected message.
- Form behavior — Verified by
  `test_dynamic_slash_and_action_use_same_action_and_ordered_form`,
  `test_form_context_prefill_beats_default_and_secret_is_never_prefilled`,
  all eight cases of `test_form_cancellation_at_each_prompt_prevents_invocation`,
  and `test_confirm_cancellation_prevents_invocation`. The action boundary
  receives ordered/coerced/defaulted text, integer, number, select, boolean,
  multiline, secret, password, optional-skip, and `submit_empty` values;
  cancellation records no invocation.
- Direct-result follow-ups — Verified by
  `test_direct_followup_reference_executes_after_rendering`,
  `test_direct_followup_preserves_message_context_and_nonpreserving_lifetime`,
  and `test_invalid_followup_binding_is_not_registered`. Exact printed
  references preserve fixed, `$form`, `$dialog`, session/message,
  `display_id`, validation, and `preserve_display` behavior.
- Automatic application notifications — Verified by
  `test_notification_hydration_dedup_and_authoritative_followup`,
  `test_notification_poll_loop_renders_without_listing_command`,
  `test_notification_cursor_recovery_hydrates_authoritative_revision`,
  `test_notification_cursor_recovery_retires_pruned_terminal_revision`, and
  `test_application_replacement_invalidates_refs_and_rehydrates_notifications`.
  Real stores/services prove startup hydration, live rendering, deduplication,
  revision supersession, terminal retirement, cursor recovery, and
  replacement hydration.
- Automatic session notifications — Verified by
  `test_inactive_session_notification_is_ignored_until_switch`. An inactive
  event is ignored, switching hydrates its pending authoritative record, and
  switching back does not replay an accepted revision.
- Authoritative notification follow-ups — Verified by
  `test_notification_hydration_dedup_and_authoritative_followup`. The printed
  reference executes parameters from a newer authoritative revision and is
  retired after resolution; malformed/unknown bindings cannot register.
- Notification UX boundary — Verified by
  `test_notification_poll_loop_renders_without_listing_command`, inactive
  session behavior, and static command inspection. Receipt neither changes the
  active session nor introduces list/pull, attention, aggregation, badge,
  sound, focus, or notification-center behavior.
- Foreground auth success and cancellation — Verified by
  `test_codex_cli_command_runs_complete_foreground_device_flow`,
  `test_standalone_foreground_interrupt_cancels_once_and_exits_130`,
  `test_cancel_login_stops_pending_flow_and_keeps_credentials_absent`, and
  `test_stale_attempt_cannot_commit_credentials`. The 19-test gated ChatGPT
  package run passed with two manual tests deselected. Generic terminal module
  inspection found no provider names or protocol branches.
- Sensitive data — Verified by
  `test_dynamic_slash_and_action_use_same_action_and_ordered_form`,
  `test_form_context_prefill_beats_default_and_secret_is_never_prefilled`, and
  `test_standalone_help_never_exposes_sensitive_form_flags`, and
  `test_sensitive_values_are_redacted_from_action_errors`. Canary secrets
  reach the action only through masked interactive input and are redacted from
  successful displays and exceptions; they do not appear in captured output,
  help, completion, or canonical commands.
- Reload and compatibility — Verified by
  `test_application_replacement_invalidates_refs_and_rehydrates_notifications`,
  the 70-test terminal/headless regression slice, 639-test core package run,
  54-test cloud package run, and public `validate-cloud --help` subprocess.
  Replacement removes the old route/reference, exposes the new route, and
  rehydrates authoritative notifications. The final application package run
  passed 610 tests with one intentional skip and 117 marker deselections.

### Additional implementation verification

- Run focused core application-plugin/action/notification tests, terminal
  application/event/rendering tests, CLI subprocess integration tests,
  frontend SDK action/notification contract tests, `cloud-agent-app` tests,
  and `chatgpt-auth-app` tests before the default core and application suites.
- Run Ruff on changed Python packages and Pyright when public UI/action types
  change; run the frontend SDK typecheck/tests if shared TypeScript contracts
  change.
- Verify hydration/event interleavings around startup, session switch,
  application replacement, and cursor expiry do not miss or double-render a
  revision.
- Verify reference registries are bounded by their approved lifetime, retain
  no application objects from an old generation, and never store plaintext
  secret input.
- Verify foreground polling and notification observation are bounded and do
  not busy-loop; application/plugin close still releases active workers and
  listeners.

Verification status:

- Passed: Ruff on all changed production/test Python files; Black on all new
  Python files; `py_compile`; `git diff --check`.
- Incomplete (pre-existing baseline): Pyright reports existing cross-import
  identity and strict-typing diagnostics. Newly added command catalog and
  action-binding APIs report no diagnostics; new terminal narrowing issues
  found by the check were corrected.
- Incomplete (environment): `npm --workspace
  @crystal-lattice/frontend-sdk test` failed before collection because
  `vitest/config` is unavailable in this worktree's Node dependency layout.
  No shared TypeScript contract changed.

## Implementation Notes

- 2026-10-19: Execution approved with all six recommendations. The first auth
  consumer uses `codex`, exposes no method argument for the device-only flow,
  and defers logout.
- 2026-10-19: Command discovery now normalizes action-backed UI elements in the
  application layer. Legacy `get_commands()` declarations are adapted only for
  `cli_command`; slash discovery reads the active session's UI schema and never
  mutates the static decorator registry.
- 2026-10-19: The terminal's installed editable package pointed at a sibling
  checkout. Decisive test commands explicitly prepend this worktree's
  `application/python`, `core/python`, and application test-fixture paths to
  `PYTHONPATH`; ordinary focused regression runs that did not need new imports
  were also recorded.
- 2026-10-19: Application notification events are global while ordinary
  terminal polling is session-filtered. The implementation therefore owns a
  separate global notification cursor, combines it with authoritative
  application/current-session hydration, and deduplicates by scoped identity
  and revision.
- 2026-10-19: Top-level and interactive commands, direct action results, and
  notifications now share one action-result renderer. Standalone command
  forms apply the same fixed/mapped parameter contract before dispatch;
  required sensitive fields remain interactive-only and never become command
  flags.
- 2026-10-19: Follow-up registration now resolves the referenced action
  binding without executing it. Direct references are retired by display
  identity and generation, while notification references are rebuilt from
  authoritative current revisions immediately before invocation.
- 2026-10-19: Focused production-path tests cover nested public CLI dispatch,
  dynamic help/completion, every form-prompt cancellation stage, canonical
  message context, all action scopes, direct form/dialog references,
  application replacement, cursor recovery, inactive sessions, automatic
  notification rendering, authoritative follow-ups, and standalone foreground
  interruption.
- 2026-10-19: Frontend SDK compatibility verification is incomplete. The
  package test command failed before collection because this worktree could
  not resolve `vitest/config`; no shared TypeScript contract changed, and no
  dependency install or lockfile mutation was performed.
- 2026-10-19: The first complete application run exposed repeated
  notification-poll errors in a production PTY progress harness that implements
  only the older terminal façade. Notification observation is now
  capability-checked; the exact PTY regression and the combined 31-test
  terminal/security slice pass. A clean package rerun is in progress.
- 2026-10-19: Cursor-recovery hydration now reconciles known notification
  identities against each successfully loaded active snapshot. This retires a
  stale follow-up immediately even when its terminal revision event was
  pruned; failed snapshot loads do not retire known references.
- 2026-10-19: Dynamic slash help and completion include full-path aliases and
  declared non-sensitive form arguments. Secret/password names and values are
  excluded. Multiline action prompts explicitly bind Ctrl-D to submission and
  Escape to cancellation.
- 2026-10-19: Session command catalogs validate application,
  provider-extension, or feature action owners through the normal
  no-execution resolver with current-session context. ChatGPT cancellation now
  joins its attempt worker for up to one second, so generic interruption waits
  for bounded provider-owned cleanup and publishes cancellation once.
- 2026-10-19: During verification, a concurrent resend workstream added
  changes to initially clean headless-runtime/docs/test files and also touched
  the shared top-level entrypoint. Those user-owned edits were preserved and
  excluded from this task's claimed implementation; the final application
  package run exercised the combined worktree successfully.

## Completion Notes

- Outcome: completed the approved plugin-driven command and terminal action
  architecture. Actions remain procedures; applicable UI elements alone expose
  top-level commands, slash commands, `/action`, direct follow-ups, and
  notification follow-ups. Legacy `get_commands()` remains CLI-only.
- Terminal UX: implemented nested command paths/aliases, deterministic
  collision rejection, dynamic help/completion with safe arguments, the exact
  `/action` grammar and canonical message indexes, ordered typed forms,
  cancellation, disabled reasons, shared rendering, opaque executable
  references, and exact-value secret redaction.
- Notifications: implemented automatic application/current-session rendering,
  startup/replacement/session-switch/cursor-recovery hydration, scoped
  identity/revision convergence, inactive-session filtering, terminal-state
  reconciliation, and authoritative follow-up rereads. No listing command,
  pull-only UX, attention state, aggregation, focus change, badge, sound, or
  notification center was added.
- Foreground consumer: `chatgpt-auth-app` now contributes
  `crystal-lattice auth login codex` and `/login codex` for the device-only
  flow, with no method argument and no logout command. Start/status/cancel use
  ordinary actions; cancellation is attempt-scoped with bounded worker cleanup,
  and stale workers cannot replace newer credentials.
- Maintained documentation was updated for plugin authors, actions,
  notifications/displays, terminal users and maintainers, and ChatGPT auth.
  `validate-cloud` documentation did not change because its compatibility help
  remained unchanged.
- Decisive verification passed:
  - application package: 610 passed, 1 skipped, 117 deselected;
  - core package: 639 passed, 27 deselected, 1 expected xfail;
  - ChatGPT auth package with `not manual_integration`: 19 passed,
    2 deselected;
  - cloud-agent app package: 54 passed;
  - combined core/terminal/PTTY focused slice: 43 passed;
  - Ruff, `py_compile`, `git diff --check`, and Black checks for all new Python
    files passed.
- Incomplete supplementary evidence:
  - Pyright still reports the repository's pre-existing cross-import identity
    and strict-typing baseline. New command-catalog/action-binding diagnostics
    were cleared, but the project-wide typecheck is not green.
  - Frontend SDK tests did not collect because `vitest/config` is unavailable
    in this worktree's Node dependency layout. No TypeScript contract changed,
    and dependencies/lockfiles were not modified.
- Verification findings resolved during execution: standalone mapping/shared
  rendering, invalid follow-up registration, built-in namespace-prefix
  collisions, PTY harness notification capability detection, pruned terminal
  notification reconciliation, successful/error secret redaction, explicit
  multiline Ctrl-D submission, alias/argument help/completion, session action
  owner validation, and bounded auth-worker cancellation.
- No requirement questions remain. Browser OAuth, Anthropic adoption,
  mobile/desktop command frontends, notification-center behavior, and logout
  command adoption remain outside this task as approved. No commit was
  created.