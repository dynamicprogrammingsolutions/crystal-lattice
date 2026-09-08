# Configuration composition implementation

The application configuration composition contract is defined by the
[application configuration composition specification](specifications/application-configuration-composition/index.md).
This page maps the delivered implementation and does not redefine that
contract.

## Ownership

`core/python/agent_app` owns:

- placeholder resolution;
- static mixin expansion;
- provider-to-agent configuration composition;
- recursive merge policy;
- model-selected variants;
- effective request configuration.

Providers and feature plugins receive an already-resolved effective mapping.
They do not interpret `$variants`, `$when`, `$matches`, or `$merge`.

## Maintainer entry points

- `agent_app/config.py`: loading, mixin expansion, provider/agent composition,
  effective request config, and application integration helpers;
- `agent_app/config_merge.py`: immutable recursive shallow/deep merge engine;
- `agent_app/config_variants.py`: condition validation, selection, nested
  variant resolution, and topology protection;
- `agent_app/application_future.py`: startup validation, session model
  overrides, initial core construction, and UI-effective config.

`plugins/feature-request-options` retains its package-local helper for merging
flat UI overrides into nested `request_options`. It does not depend on
`agent_app`; configuration-language controls have already been resolved before
the feature runs.

## Resolution sequence

1. Resolve environment and file placeholders.
2. Expand static mixins.
3. Compose provider defaults and the selected agent.
4. Preview explicit overrides to create the immutable variant selector.
5. Resolve matching variants from the unchanged base config.
6. Apply explicit session/request overrides last.
7. Pass the effective mapping to core/plugin resolution and UI generation.

The base agent mapping remains cached and unchanged. Each effective resolution
therefore starts cleanly when the session model changes.

## Merge invariants

- Shallow mode replaces a colliding direct value.
- Deep mode recursively merges colliding mappings.
- Parent `$merge` policy can assign shallow/deep behavior to individual direct
  sibling keys.
- Nested mappings may define another policy.
- Arrays and scalars replace and arrays are not traversed for controls.
- Inputs are not mutated.
- Existing `mixin_merge` remains a root compatibility spelling.

## Variant invariants

- Exact scalar conditions and `$matches` use top-level selector fields.
- Every condition in one resolution observes the same immutable selector.
- Matching entries apply in declaration order.
- Explicit overrides apply after variants.
- Root variants cannot modify provider/plugin topology.
- Control keys do not reach effective provider configuration.

## Verification

Primary deterministic coverage:

- `core/python/tests/test_application_config_composition.py`;
- `core/python/tests/test_application_layer_config.py`.

Application/default-config coverage:

- `application/python/tests/test_default_config_effective_agent_configs.py`;
- `application/python/tests/test_claude_system_message_helpers.py`;
- `application/python/tests/test_terminal_application_default_config_anthropic_integration.py`.

Consumer behavior is documented under
`application/python/docs/configuration*.md`.