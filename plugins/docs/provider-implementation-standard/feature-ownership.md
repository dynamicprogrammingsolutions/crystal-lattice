# Provider feature ownership

## Provider extensions

Use a provider extension for optional behavior expressed in the provider's
native protocol, including:

- tools;
- reasoning/thinking;
- usage and pricing display;
- prompt caching;
- provider-native attachments;
- web/search server tools;
- service tiers or speed controls;
- provider-native compaction.

The extension owns:

- `get_config_schema`;
- `get_ui_elements`;
- tags and `required_tags`;
- capability/model gating;
- normalized feature state;
- request shaping;
- hot-path accumulation and finalization;
- public message metadata;
- feature tests and user documentation.

## Inseparable transport mechanics

Some features need work inside the provider's active transport loop, such as:

- feature-specific retries;
- alternate SDK calls;
- closing a feature-specific stream;
- parsing an event shared by several extensions;
- retaining raw usage for later extension formatting.

The provider may perform those mechanics when the extension has enabled the
feature and written normalized state. The provider does not define duplicate
config, UI, or enablement.

This keeps the feature independently selectable even when the network code
cannot be physically moved out of the provider.

## Direct request-option features

When a provider feature maps directly to request-body keys and preserving the
native wire shape is important, the generic request-options feature may own
request injection and declarative UI. The provider-specific extension may then
own only:

- provider-native response interpretation;
- streaming accumulation;
- native-history reconstruction and continuation state;
- public metadata;
- capability/configuration documentation and tests.

This boundary is appropriate for versioned or compatible protocols where one
normalized feature schema would hide valid request shapes. The provider still
owns transport-only mechanics such as choosing a stable or beta SDK method,
composing beta headers, reserving history-owned request fields, and routing
unknown compatible fields through an SDK escape hatch.

Package documentation must identify:

- which request fields are passed through directly;
- which fields are reserved by the provider;
- how beta or alternate transports are selected;
- which compatible endpoint configurations have been tested with each request
  shape.

## Feature plugins

Use a feature plugin for provider-portable cold-path behavior that can operate
through stable core/provider contracts, such as:

- generic request options;
- system-message rendering;
- provider-independent conversation preparation.

Do not use a generic feature to hide a provider-specific wire protocol.

## Application plugins

Use an application plugin for behavior requiring:

- credential acquisition and persistence;
- login/status/logout actions;
- background processes;
- multi-session workflows;
- session persistence or reconciliation;
- notifications;
- deep links and client-visible actions.

The provider consumes the resulting credential or request contract without
owning the UI lifecycle.

## Tools

Tool plugins own executable tool behavior, schemas, result formatting, and
tool-specific display. Provider or provider-extension code owns converting
schemas, calls, and result messages to the active provider protocol.

Do not fork a tool bundle solely because a new compatible provider is added.
Fix provider-boundary interop unless the tool's actual public contract must
change.

## Naming

Use concise runtime names. Package names may identify compatibility scope, but
provider IDs and class names should remain natural in configuration and code.

Keep related extension names consistent:

```text
ExampleProvider
ExampleToolsExtension
ExampleReasoningExtension
ExampleUsageExtension
```