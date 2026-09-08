# Decision: configuration-language and merge policy

## Context

Application configuration already supports static mixins with node-wide
shallow or deep merge. Model-specific provider settings currently require
duplicated agents or provider-owned model branching.

Conditional configuration must also compose nested request options, UI, beta
identifiers, and other already-loaded plugin settings. Merge behavior needs to
be consistent with existing mixins and extensible without distributing
condition logic through providers and features.

## Decision

Use `$`-prefixed configuration-language controls:

- `$variants` for ordered conditional overlays;
- `$when` for conditions;
- `$matches` for regular-expression matching;
- `$merge` for recursive parent-scoped merge policy.

`$merge` controls ordinary sibling keys. It supports:

- `"shallow"` or `"deep"` shorthand;
- an object with `default`, `shallow`, and `deep`;
- nested policies declared by nested mappings.

One shared merge interpreter serves mixins, provider-to-agent composition, and
variants. Existing `mixin_merge` remains a root compatibility alias.

Variant conditions use one immutable preview of base configuration plus
explicit overrides. Matching variants apply in order, and explicit overrides
apply after variants.

## Consequences

- Static reuse and dynamic model selection use one composition model.
- A deep merge can select shallow behavior for individual direct keys.
- Future condition operators are isolated behind a registry.
- Future key-specific array operations can extend the parent policy without
  putting directives inside arrays.
- Existing mixin defaults and configurations remain valid.
- Providers and RequestOptionsFeature do not implement condition selection.
- Array-specific merge operations and arbitrary expressions remain outside
  the initial implementation.