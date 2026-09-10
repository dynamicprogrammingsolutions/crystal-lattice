# Application Configuration Variants And Recursive Merge

Define and implement one application-owned configuration composition language
for existing mixins and model-selected variants, then use it to consolidate the
direct Anthropic default agents.

Parent Task: `tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

## Requirements checklist

- [x] Application configuration supports ordered `$variants` at provider,
  agent, mixin, and nested mapping scopes.
- [x] Variant conditions support exact scalar matching and the `$matches`
  regular-expression operator against the immutable effective-config selector.
- [x] `$merge` supports string shorthand and a parent-scoped object form with
  a default mode plus key-specific `shallow` and `deep` lists.
- [x] The recursive merge implementation is shared by mixin expansion,
  provider-to-agent composition, and variant overlays.
- [x] Existing `mixin_policy`, `mixin_refs`, and `mixin_merge` configurations
  retain their current behavior and compatibility.
- [x] Variant selection is reevaluated after model overrides, explicit
  session/request overrides win, and prior-model values do not leak.
- [x] Variants cannot change provider or plugin topology after startup.
- [x] One `claude-anthropic` default agent selects the correct supported
  reasoning, effort, beta, context-management, and UI configuration for
  Claude 4.5 and newer model families without a separate Sonnet agent.
- [x] Deterministic tests cover the merge interpreter, mixins, variants,
  effective config, model switching, diagnostics, and default configuration.
- [x] Consumer configuration documentation is split into focused current-state
  pages for plugin configuration, placeholders, mixins, variants, and system
  messages while preserving the existing configuration landing URL.

## Specification

- `core/python/docs/development/specifications/application-configuration-composition/index.md`
- Requirements: `ACFG-001` through `ACFG-012`

## Scope

This subtask owns:

- the reusable merge interpreter in `agent_app`;
- recursive `$merge` semantics;
- current mixin compatibility and migration to the shared interpreter;
- `$variants`, `$when`, and `$matches`;
- effective-config ordering and diagnostics;
- default direct Anthropic model variants and agent consolidation;
- application-package consumer documentation migration.

It does not own:

- arbitrary expression evaluation;
- conditional provider or plugin package loading;
- provider capability discovery;
- provider-owned model-name branching;
- variants embedded inside arrays;
- array append, prepend, or uniqueness operations in the initial
  implementation;
- changes to provider request-option semantics after effective config is
  resolved.

## Supporting facts

- `core/python/agent_app/config.py` already implements shallow and deep mapping
  merge for mixin expansion and provider-to-agent composition.
- Existing mixins support `mixin_policy.default_merge`,
  `mixin_policy.max_depth`, ordered recursive `mixin_refs`, and node-local
  `mixin_merge`.
- Current shallow merge replaces colliding nested values at the direct key,
  while current deep merge recursively merges mappings. Lists and scalars
  replace in both modes.
- `plugins/feature-request-options` has a separate narrow deep-merge helper for
  inflating flat UI overrides. It must not import `agent_app`; configuration
  directives are resolved before that feature runs.
- `resolve_request_config` currently performs a shallow base/override merge and
  returns the base mapping unchanged when no overrides exist.
- Application session UI is generated from effective config, so model-selected
  variants can update request-option controls when effective config resolution
  evaluates them after model overrides.
- Public application configuration is currently concentrated in
  `application/python/docs/configuration.md`.

## Execution plan

Status: Approved

Implement the specification in three bounded work areas.

First, extract the existing application merge behavior into a pure merge
interpreter. Preserve current shallow-by-default mixin behavior while adding
recursive parent-scoped `$merge` directives. A mapping may use
`"$merge": "deep"` or an object such as:

```json
{
  "$merge": {
    "default": "deep",
    "shallow": ["request_options"],
    "deep": ["headers"]
  }
}
```

The object controls its ordinary sibling keys. Nested mappings may define
their own policy for their direct children. Arrays and scalars replace in the
initial implementation. Keep the policy shape extensible for later
key-specific array operations, but do not add append/prepend/unique behavior
in this subtask.

Second, add an isolated variant interpreter. `$variants` may appear in a
provider, agent, mixin, selected variant overlay, or nested mapping, but is not
interpreted inside arrays. Each entry uses `$when`; ordinary entry keys form
the overlay. Exact scalar conditions compare directly, and
`{"$matches": "..."}` uses a validated regular expression. All conditions use
one immutable selector built from the base config plus explicit overrides.
Matching variants apply in declaration order. Resolve variants from a clean
base on every effective-config calculation, then apply explicit overrides
last.

Third, add a reusable `claude_anthropic_model_variants` mixin and retain one
`claude-anthropic` agent, defaulting to the primary Sonnet model. Initial
Claude-specific variants cover:

- Haiku, Sonnet, and Opus 4.5 manual thinking with budget and display controls;
- the interleaved-thinking beta header for Sonnet and Opus 4.5, excluding
  Haiku;
- Opus 4.5 effort choices;
- Sonnet and Opus 4.6 adaptive thinking, context-management keep-all, and
  `low`/`medium`/`high`/`max` effort;
- Sonnet 5 and supported Opus 4.7-or-newer adaptive thinking,
  context-management keep-all, and all five effort levels;
- separate always-thinking/current Opus handling where a disable control would
  permit an invalid effort combination.

Unknown or unmatched Anthropic-compatible models receive no inferred thinking
configuration. Raw request options remain available.

### Implementation decisions and open questions

- Decision: the collection key is `$variants`, not `$rules`.
- Decision: conditions use `$when`; regex matching uses `$matches`.
- Decision: a scalar condition means exact equality and multiple condition
  fields use logical AND.
- Decision: conditions initially inspect top-level effective-config fields;
  dotted paths and arbitrary expressions are deferred.
- Decision: `$merge` is a parent-scoped policy for ordinary sibling keys.
- Decision: `$merge` accepts `"shallow"`/`"deep"` shorthand and an object with
  `default`, `shallow`, and `deep`.
- Decision: key lists name direct siblings only. Nested scopes declare their
  own `$merge` rather than using dotted paths.
- Decision: variant overlays default to deep merge; mixins preserve
  `mixin_policy.default_merge`, whose built-in default remains shallow.
- Decision: arrays and scalars replace in shallow and deep modes. Array
  append/prepend/unique operations are deferred without reserving an
  incompatible syntax.
- Decision: `mixin_merge` remains a root compatibility alias. Conflicting
  `mixin_merge` and root `$merge` declarations are configuration errors.
- Decision: `$variants`, `$when`, `$matches`, and `$merge` are interpreted only
  in their defined configuration-language scopes and are removed from
  effective runtime config.
- Decision: variant overlays cannot modify `provider`, plugin package specs,
  plugin enablement lists, mixin references, or mixin merge policy.
- Decision: RequestOptionsFeature retains its package-local nested override
  helper; it receives only already-resolved configuration.
- Decision: the direct Anthropic defaults use configuration variants rather
  than provider-owned model pattern logic.
- Decision: the consolidated direct Anthropic agent defaults to
  `claude-sonnet-5`; the hosted low-cost smoke selects Haiku 4.5 through a
  session model override.

### Documentation

The normative target remains in:

- `core/python/docs/development/specifications/application-configuration-composition/`

When implementation is delivered, migrate
`application/python/docs/configuration.md` into this consumer structure:

- `configuration.md`: concise landing page, configuration layers, and links;
- `configuration-plugins.md`: plugin package specs, loading layers,
  enablement, policy, and migration guidance;
- `configuration-placeholders.md`: environment/file placeholders, derived
  variables, and `$raw`;
- `configuration-mixins.md`: reusable fragments, precedence, recursion,
  `mixin_policy`, compatibility `mixin_merge`, and recursive `$merge`;
- `configuration-variants.md`: `$variants`, `$when`, `$matches`, merge policy,
  precedence, model-selection examples, restrictions, and troubleshooting;
- `configuration-system-messages.md`: system-message templates, runtime code,
  variables, conditions, and default-config examples.

Keep `application/python/docs/configuration.md` as the public landing page so
the existing route remains valid. Move content rather than copying complete
sections into multiple maintained pages. Update:

- `application/python/docs/index.md`;
- `application/python/README.md`;
- relevant development implementation documentation;
- documentation-site navigation or registry inputs only if the authored page
  split requires them.

Consumer pages describe only committed behavior and do not expose task,
requirement, approval, or implementation-stage language. Add the variants page
with the implementation commit, not during target-only planning.

### Task checklist

- [x] Extract a package-owned recursive merge interpreter from current config
  helpers.
- [x] Preserve and retest existing mixin expansion and provider/agent merge
  behavior.
- [x] Add recursive parent-scoped `$merge` parsing, validation, and stripping.
- [x] Add the isolated `$variants` condition interpreter.
- [x] Integrate variants into effective config and initial session/core
  construction.
- [x] Reject runtime topology changes and malformed special-key expressions.
- [x] Add the Claude model-variant mixin and consolidate direct Anthropic
  agents.
- [x] Add focused merge, mixin, variant, effective-config, UI, and default
  configuration tests.
- [x] Migrate and verify consumer configuration documentation.
- [x] Update specification requirements and evidence.
- [x] Run package, application, documentation preparation, and documentation
  build verification.

### Requirement verification

- `ACFG-001` and `ACFG-002`: existing mixin and root merge behavior remains
  covered by the application-layer configuration tests.
- `ACFG-003` through `ACFG-005`: pure merge tests prove recursive defaults,
  key-specific shallow/deep modes, directive stripping, immutable inputs, and
  compatibility aliases.
- `ACFG-006` through `ACFG-008`: variant tests prove exact/regex selection,
  nested placement, ordered overlays, immutable selectors, override
  precedence, topology protection, and diagnostics.
- `ACFG-009`: one session changes among representative Claude 4.5, 4.6, and
  newer models and receives the matching request options, betas, and UI without
  stale values.
- `ACFG-010`: default-config tests prove one direct Anthropic agent replaces
  the separate model-specific agents while OpenRouter Claude remains.
- `ACFG-011`: consumer documentation examples are checked against resolved
  config fixtures and the documentation build.
- `ACFG-012`: existing plugin, application, and default-config suites pass
  without changing plugin loading or request-option ownership.

### Additional implementation verification

- Test exact error paths for invalid regular expressions, invalid merge modes,
  duplicate key-mode assignments, unknown condition operators, and prohibited
  overlay keys.
- Test maximum merge/variant nesting depth.
- Test that arrays replace and are not recursively interpreted.
- Test that `$merge`, `$variants`, `$when`, and `$matches` never reach provider
  request configuration or generated UI schemas.
- Test that provider and agent configurations using legacy `mixin_merge`
  produce the same effective mappings as before.
- Run `pytest core/python/tests/test_application_layer_config.py -q`.
- Run the feature-request-options package tests.
- Run focused default-config tests, then `pytest application/python/tests -q`.
- Run documentation preparation and a normal MkDocs build.

## Implementation Notes

### 2026-08-31

- Added `agent_app/config_merge.py` as the shared immutable recursive merge
  interpreter and `agent_app/config_variants.py` as the isolated condition and
  variant interpreter.
- Static mixin composition preserves nested merge directives until
  provider-to-agent composition consumes them. Final runtime config strips all
  merge and variant controls.
- `resolve_request_config` now builds one immutable selector, resolves variants
  from the unchanged base, and applies explicit overrides last.
- Application startup validates mixin, merge, and variant errors as fatal
  configuration errors with exact paths.
- New-session and agent-switch core construction uses the initial effective
  config so model-selected tags and UI are available immediately.
- The bundled config now has one direct `claude-anthropic` agent, defaults to
  `claude-sonnet-5`, and uses `claude_anthropic_model_variants` for Claude 4.5,
  4.6, Sonnet 5, current Opus, Fable, and Mythos profiles.
- The hosted default-config smoke explicitly selects
  `claude-haiku-4-5-20251001`, preserving the lower-cost verification path.
- Consumer configuration documentation was split while retaining
  `configuration.md` as the stable landing page.

## Completion Notes

Completed the approved configuration-composition implementation.

Requirement evidence:

- `ACFG-001` through `ACFG-008`: shared merge/variant implementation and 38
  focused composition plus legacy-mixin tests.
- `ACFG-009` and `ACFG-010`: default config raw/effective tests, dedicated
  model-switch/UI integration, Claude helper tests, and hosted Haiku Read-tool
  smoke.
- `ACFG-011`: focused consumer pages, package indexes, implementation map,
  successful documentation preparation, and successful MkDocs build.
- `ACFG-012`: Core fast suite `499 passed, 26 deselected, 1 xfailed`;
  application fast suite `370 passed, 92 deselected`; request-options package
  `27 passed`.

Additional verification:

- Pyright reports zero errors for the new merge/variant modules and their
  focused tests.
- Ruff, Black, JSON parsing, and `git diff --check` pass for the scoped work.
- The real Anthropic default-config smoke passes after selecting Haiku through
  a session override.

Findings and deviations:

- Nested merge directives require two-stage handling: preserve during static
  mixin composition, consume during final provider-to-agent composition.
- The broader existing
  `test_default_config_effective_agent_configs_stay_intact` integration test
  still fails before its agent assertions because two unrelated session-search
  UI elements omit `main_search: false`. The new Claude variant integration
  test is separate and passes.
- The documentation build retains existing navigation, source-test-link,
  absolute-link, and generated-reference warnings.

## Post-completion follow-up

The final full Core run after adding the last three edge-case tests completed
with `502 passed, 26 deselected, 1 xfailed`.
Follow-up (mixin application policy change, 2026-09-08, user-directed from
task 010): the mixin-carried directive semantics were redesigned. A
referenced mixin's own root `$merge` now governs that mixin's merge into its
referrer and is consumed by that merge action — neither the root directive
nor nested `$merge` directives inside the referenced mixin persist into the
referrer's resolved configuration, and directive-less references keep using
the referrer's root policy. Previously a referenced mixin's root directive
was popped and replaced by the referrer's at reference time, and nested
directives survived into the resolved agent to govern later merges (the
pinned `test_nested_mixin_merge_directive_survives_until_provider_agent_merge`
behavior). That use case now declares the nested policy on the agent itself.
The specification gained a "Mixin application policy" section and requirement
`ACFG-013`; `test_nested_mixin_merge_directive_survives_until_provider_agent_merge`
was replaced by own-merge governance, consumption, agent-carried, and chained
mixin tests; the consumer mixin guide documents the new behavior. No shipped
config relied on the old semantics (the claude bash presets are the first
directive-carrying mixins and now carry their own per-key policy).
