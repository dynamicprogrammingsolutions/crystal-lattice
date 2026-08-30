# Decision: package identity and extension boundaries

## Context

The package must be recognizable as an Anthropic-compatible implementation
without making long compatibility-oriented names part of normal configuration
or class APIs. Provider-specific features also need consistent ownership so
transport code does not accumulate configuration and UI concerns.

## Decision

- Directory: `plugins/anthropic-compatible`
- Distribution: `anthropic-compatible-provider`
- Python module: `anthropic_plugins`
- Provider ID: `anthropic`
- Provider class: `AnthropicProvider`
- Extension class names use the short `Anthropic...Extension` form.

The provider owns transport, auth consumption, model discovery, native
conversion, stream reduction, cancellation, and raw error parsing.

Provider extensions own feature configuration, UI, enablement, request
shaping, public metadata, tests, and documentation. The provider may execute
inseparable transport mechanics only through normalized extension state.

## Consequences

- User config stays concise.
- Package naming advertises compatible-endpoint support.
- Optional features can be reviewed, tested, and disabled independently.
- Provider mechanics may still contain narrow hooks for retries or event
  parsing without becoming the feature's public owner.