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
notification and action-response `modal` presentation to inline cards in the
message/detail area.

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

Every host preserves fixed parameters, parameter mappings, embedded forms, and
submitted form values when invoking `run_action`.

Historical replay is read-only by default. Mutating actions require explicit
historical validity and server-side lifecycle/revision validation.

Displays must not expose credentials or sensitive configuration values.