# Request options UI

This package-owned specification defines the declarative
`request_options_ui` contract provided by the `feature-request-options`
plugin. It covers the existing shorthand forms, nested request-option paths,
flat session overrides, and the target opt-in descriptor that exposes selected
fixed-choice request options through the standard rich composer UI.

It does not redefine the platform rich-UI element contract or provider-owned
model discovery. The plugin generates standard config elements and applies the
shared rich-UI contract documented for plugin authors.

Specification documents:

- [Product specification](product-spec.md)
- [Requirements and evidence](requirements.md)

Related contracts:

- [Plugin UI elements](../../../../../docs/ui-elements.md)
- [Provider feature ownership](../../../../../docs/provider-implementation-standard/feature-ownership.md)

Approval and execution are tracked by
[portable rich session settings follow-up](../../../../../../tasks/20260824-direct-claude-provider-and-plugin-login/022-portable-rich-session-settings-and-model-picker-ui.md).