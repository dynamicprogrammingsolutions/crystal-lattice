# Action-display technical specification

An action display contains user-facing text or markdown, an optional title,
semantic variant, presentation, dismissibility, optional embedded form, stable
display ID, and follow-up actions.

Supported presentations:

- `banner`
- `inline`
- `modal`

Supported follow-up actions:

- `run_action`
- `open_url`
- `copy_text`
- `download_attachment_asset`
- `dismiss`

`run_action` may combine fixed parameters, parameter mappings, and submitted
form values. Connection and session context are supplied by the owning
surface.

Explicit valid presentation takes precedence over source defaults. Current
defaults are:

- application notification: `banner`;
- session notification: `inline`;
- direct action response: `modal`.

Application notifications reject `inline`. Desktop currently normalizes
notification `modal` presentation to inline cards in the message/detail area.
Direct action responses requesting `modal` open a standard desktop action
display window. Mobile continues to use its standard modal overlay.

Modal and window presentations bound lengthy bodies to the available viewport
and provide an internal scroll area. Closing a direct-display window remains a
frontend-local dismissal and does not mutate the owning session.

Dismiss behavior depends on display ownership:

- notification display: invoke the owning server notification dismissal
  operation; a frontend may optimistically cache and hide only the exact
  displayed revision while that operation is pending or retryable;
- direct action display: close the transient frontend display locally;
- historical replay: close only the replay presentation.

The display envelope or equivalent owner context must distinguish these cases.
A cached notification dismissal is obsolete when authoritative state contains
a newer pending revision. It is removed rather than retargeted; the newer
revision remains eligible for presentation.

### Dismissability

The `dismissible` field is an optional hint controlling whether the user can
dismiss the rendered display.

- Omitted or `true` means the user can dismiss the notification.
- `false` is an exceptional producer decision, not a default.

`false` is appropriate for:

- permanent or environment status indicators;
- active interactions that must remain discoverable;
- presentations where hiding would remove the only path to a required response.

Long-running operation progress should not normally use `false` merely to
preserve a Cancel action. Dismissing progress does not cancel the underlying
operation; Cancel remains an explicit follow-up action. A persistent
notification must never become a dead end: if it cannot be dismissed, it must
have a viable recovery action or reliably transition into a dismissible state.

Every host preserves fixed parameters, parameter mappings, embedded forms, and
submitted form values when invoking `run_action`.

Historical replay is read-only by default. Mutating actions require explicit
historical validity and server-side lifecycle/revision validation.

Displays must not expose credentials or sensitive configuration values.