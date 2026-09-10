# Application configuration composition technical specification

## Ownership and modules

`core/python/agent_app` owns configuration loading, placeholder resolution,
mixin expansion, provider-to-agent composition, and effective request config.

The target separates two pure components:

```text
agent_app/config_merge.py
  recursive shallow/deep merge policy

agent_app/config_variants.py
  $variants, $when, $matches, selection and validation
```

`agent_app/config.py` integrates them into existing loading and effective-config
entry points. Providers, features, tools, and frontends consume only the
resolved effective mapping.

## Existing mixin contract

Top-level mixin configuration remains:

- `mixins`: named configuration fragments;
- `mixin_policy.default_merge`: `shallow` by default or `deep`;
- `mixin_policy.max_depth`: positive recursion limit, default `16`.

Providers, agents, and mixins may use:

- `mixin_refs`: ordered mixin names;
- `mixin_merge`: root compatibility spelling for merge mode.

Resolution preserves current precedence:

1. Resolve referenced mixins recursively.
2. Apply references in declaration order.
3. Later references override earlier references.
4. Local mixin/provider/agent keys override referenced values.
5. Agent configuration overlays provider configuration.

Existing `mixin_merge` configurations retain their current result.

## Merge policy

### String form

A mapping may select one mode for its ordinary sibling keys:

```json
{
  "$merge": "deep",
  "request_options": {},
  "headers": {}
}
```

Supported modes are `shallow` and `deep`.

### Object form

A mapping may define a default and direct-key overrides:

```json
{
  "$merge": {
    "default": "deep",
    "shallow": ["request_options"],
    "deep": ["headers"]
  },
  "request_options": {},
  "headers": {}
}
```

Rules:

- `default` is optional and inherits the caller or parent default.
- `shallow` and `deep` contain unique non-empty direct sibling names.
- One key cannot appear in more than one mode list.
- Dotted paths are not interpreted.
- A nested mapping declares another `$merge` policy for its own direct
  children.
- `$merge` is removed from the resolved mapping.

### Shallow merge

Shallow merge preserves base direct keys not mentioned by the overlay. A
colliding overlay value replaces the complete direct base value, including a
nested mapping or array.

### Deep merge

Deep merge recursively merges colliding mappings. Scalars and arrays replace.
A nested overlay mapping may change the policy for its own direct children.

### Arrays

Arrays replace in both modes and are not recursively interpreted in the
initial implementation. Parent-scoped merge policy permits future
key-specific array operations without placing directives inside arrays, but
this specification does not require those operations.

### Compatibility alias

At a mixin/provider/agent root, `mixin_merge` remains a compatibility alias for
a root string `$merge`.

If both are present:

- equal modes are accepted;
- conflicting modes are a configuration error.

Mixin defaults continue to come from `mixin_policy.default_merge`. Variant
overlays default to deep merge.

### Mixin application policy

A mixin's own root `$merge` governs how that mixin merges into its referrer.
The directive is scoped to that merge action:

- a referenced mixin carrying a root `$merge` is merged under its own policy;
- a referenced mixin without a root `$merge` is merged under the referrer's
  root policy, or the `mixin_policy.default_merge` default;
- the referrer's root policy still governs the referrer's local overlay and
  any later merge actions the referrer performs, such as provider-to-agent
  composition.

Mixin-carried directives are consumed by the merge action. Neither the root
directive nor nested `$merge` directives inside the referenced mixin persist
into the referrer's resolved configuration. A referrer that needs a nested
policy for a later merge action declares that policy on itself.

## Variant language

### Collection

`$variants` is an ordered list:

```json
{
  "$variants": [
    {
      "$when": {
        "model": "example-model"
      },
      "request_options": {
        "temperature": 0.2
      }
    }
  ]
}
```

Each entry contains:

- required `$when`;
- optional `$merge`;
- ordinary overlay keys.

`$when` and `$merge` are not copied into the overlay.

### Conditions

A scalar condition uses exact equality:

```json
{
  "$when": {
    "model": "example-model"
  }
}
```

`$matches` applies a validated regular expression to a string selector value:

```json
{
  "$when": {
    "model": {
      "$matches": "^example-model-5(?:$|-)"
    }
  }
}
```

Multiple fields use logical AND. Initial conditions address top-level selector
fields only. Unknown condition operators and invalid regular expressions are
configuration errors.

### Selector and ordering

The selector is an immutable preview of:

```text
base agent config + explicit session/request overrides
```

Every condition in one resolution uses the same selector. Values introduced
by an earlier variant do not change whether a later variant matches.

Matching variants apply in declaration order. Later overlays win according to
their merge policies.

### Nested placement

`$variants` may appear in:

- mixin mappings;
- provider mappings;
- agent mappings;
- a selected variant overlay;
- nested mappings such as `request_options` or `request_options_ui`.

Mappings stored inside arrays are data and are not traversed for variants or
merge directives in the initial implementation.

## Effective-config precedence

Effective request configuration is resolved in this order:

1. Placeholder resolution.
2. Static mixin expansion.
3. Provider-to-agent base composition.
4. Preview base plus explicit overrides to build the immutable selector.
5. Recursive variant selection and overlay application against the base.
6. Explicit session/request overrides applied last.
7. Configuration-language keys removed.

Variant resolution occurs even when no explicit override exists. Changing a
session model therefore changes request options and generated UI on the next
effective-config calculation.

Resolution starts from the unchanged base each time. Settings selected for a
previous model cannot leak into another model.

## Protected topology

Variants may configure values consumed by already-loaded providers and
plugins, including request options, request-option UI, headers, beta
identifiers, limits, and feature settings.

Variants cannot modify application/plugin topology after startup, including:

- `provider`;
- `plugins`;
- `disabled_plugins`;
- `enabled_plugins`;
- `force_enabled_plugins`;
- `mixin_refs`;
- `mixin_merge`;
- `mixin_policy`.

Attempts produce path-specific configuration errors.

## Special-key scope

Registered configuration-language keys are interpreted only in their defined
positions:

- `$variants` in traversed configuration mappings;
- `$when` and `$merge` in variant entries;
- `$merge` in mixin/provider/agent and nested overlay mappings;
- `$matches` in condition expressions;
- existing `$raw` in placeholder resolution.

Unknown operators inside condition expressions are errors. Ordinary provider
payload keys are not interpreted merely because they begin with `$`.

## Validation and failure behavior

Configuration validation reports stable error mappings with:

- type;
- exact configuration path;
- bounded detail.

Invalid conditions, regular expressions, merge policies, duplicate mode
assignments, malformed variant entries, excessive nesting, and protected keys
are fatal application configuration errors.

The merge and variant interpreters do not mutate their inputs.

## Consumer documentation

Current application consumer documentation remains under
`application/python/docs/`.

The delivered structure uses:

- `configuration.md` as the stable landing page;
- `configuration-plugins.md`;
- `configuration-placeholders.md`;
- `configuration-mixins.md`;
- `configuration-variants.md`;
- `configuration-system-messages.md`.

Consumer pages describe only implemented behavior. This specification remains
the target source while requirements track implementation and documentation
evidence.

## Verification

Verification includes:

- pure merge and variant unit tests;
- regression tests for current mixins;
- provider-to-agent and effective-request config tests;
- session model-switch and UI tests;
- default direct Anthropic config tests;
- consumer example checks;
- application package tests;
- documentation preparation and build.