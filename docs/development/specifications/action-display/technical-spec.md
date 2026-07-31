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

For the implemented baseline, `dismiss` closes the current display locally.
When the display belongs to a persisted notification, local dismissal does not
resolve that notification.

Displays must not expose credentials or sensitive configuration values.