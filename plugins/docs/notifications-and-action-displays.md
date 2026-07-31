# Notifications and action displays

Use this guide to choose the correct plugin-facing mechanism. Normative fields
and lifecycle behavior are defined by the root notification and action-display
specifications.

| Intent | Mechanism |
|---|---|
| Application/connection state during the owner lifetime | Application notification |
| Persistent session-specific state | Session notification |
| Immediate result of the current action | Direct action `display` |
| Best-effort notice emitted during tool work | Tool `notification_sink` |

## Session notification

Application plugins may call the session notification methods on
`AgentApplication`. Tools use `context["notification_sink"]`, which contains
failures rather than aborting the request.

Use a stable `key` when later creation should update one pending lifecycle
item. Resolve the notification when the underlying condition is no longer
active.

## Application notification

Application notifications are stored by the stable application owner. They
survive replacement of `AgentApplication` but not owner-process restart.
Application notifications support banner and modal presentation; inline is
rejected.

## Direct action display

Return `result.display` when the content is only the immediate result of the
current action and does not need notification persistence or lifecycle events.

## Presentation and actions

Displays support banner, inline, and modal presentation plus semantic
info/success/warning/error variants. Follow-up actions may run another action,
open a URL, copy text, download an attachment asset, or dismiss the current
display.

Embedded forms use the common form schema. `run_action` mappings may read
submitted values through `$form.<name>`.

## Safety

Never include credentials, provider keys, secret configuration, or private
runtime state in titles, bodies, source metadata, displays, events, or action
results.

## Demonstration packages

The non-default dummy application-notification, session-notification, and
action-display plugins provide deterministic examples for tests and manual
smoke checks. They are not production defaults.