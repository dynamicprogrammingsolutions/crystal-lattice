# Plugin Authoring and Public Contract Documentation

Derive concise public notification/action-display references and practical
plugin authoring guidance from the authoritative root specifications.

## Requirements checklist

- [ ] Shared plugin documentation includes a decision guide for application
  notifications, session notifications, direct action displays, and tool
  notification sinks.
- [ ] The shared plugin guide is understandable and usable on its own, with
  current APIs, required fields, complete examples, lifecycle behavior,
  presentation, failure boundaries, security guidance, and test commands.
- [ ] Plugin examples link to and conform to the root `NTF-*` and `DSP-*`
  contracts without requiring plugin authors to read internal specification
  pages before using the documented APIs.
- [ ] Public lookup material is either generated from authoritative shapes or
  kept to concise field/event/action tables without lifecycle duplication.
- [ ] Existing action and application-plugin docs link to the new guide and
  remove or clearly label duplicated normative text.
- [ ] Application-config plugin documentation covers configuration, actions,
  allowlisting, environment precedence, rollback, current security boundary,
  and tests.
- [ ] The three dummy plugin READMEs document purpose, actions, presentation
  coverage, non-default status, and test commands without adding unnecessary
  specification trees.
- [ ] Sensitive-value guidance is explicit in plugin and public reference docs.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:
`tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`

## Approved artifacts

```text
plugins/docs/
└── notifications-and-action-displays.md
```

Update existing:

- `plugins/docs/actions.md`
- `plugins/docs/application-plugins.md`
- `plugins/docs/index.md`
- `plugins/application-config-app/README.md`
- README files in the three dummy notification/display plugins.

## Plugin decision guide

Document:

| Plugin intent | Mechanism |
|---|---|
| Global transient application state | Application notification |
| Persistent session-specific state | Session notification |
| Immediate result of the current action | Direct action `display` |
| Best-effort notice emitted by a tool | Tool `notification_sink` |

Include:

- complete current application/session/tool examples;
- concise current record fields and backend-added fields;
- create/update/dismiss/resolve/expire examples;
- retention selection and history consequences;
- stable keys and deduplication;
- presentation and variant selection;
- follow-up action examples;
- model visibility;
- event/persistence/reconnect expectations;
- historical action safety and Show again behavior;
- interaction nondismissibility and response lifecycle boundaries;
- application-plugin error responsibility versus sink failure containment;
- no secrets in titles, bodies, source metadata, displays, events, or action
  results.

Clearly separate currently implemented APIs from planned lifecycle extensions.
Do not present proposed dismissal, retention, history, or interaction methods
as available runtime APIs before implementation.

## Public reference content

Defer separate hand-maintained reference pages in the first baseline. If
lookup pages are added later, keep them concise:

- normalized field tables;
- lifecycle event names;
- application/session scope comparison;
- action-display and follow-up action tables;
- compatibility rules;
- minimal valid examples;
- links to product/technical specifications and plugin guide.

Use tested schemas/examples when practical. The root specifications remain
authoritative if explanatory text differs.

## Small plugin README content

`plugins/application-config-app`:

- application config snippet;
- reload and provider-key actions;
- editable-key/provider mapping;
- process environment precedence;
- dotenv write and rollback;
- current Stage 1 security limitations;
- package test command;
- root reload-spec and plugin-guide links.

Dummy plugins:

- explicitly non-default/non-production purpose;
- action IDs and inputs;
- lifecycle/presentation/variant behavior demonstrated;
- how integration tests enable them;
- focused package test command;
- shared guide link.

Do not create package-local `docs/` trees for these small plugins unless their
README content later becomes too large.
