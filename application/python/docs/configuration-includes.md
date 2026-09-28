# Configuration includes

Any configuration object may carry a `"$include"` key referencing a JSON file.
The file's object is merged into that object, and the control key is consumed,
so downstream configuration sees only the merged result.

## Basic use

```json
{
  "providers": {
    "ollama": {
      "provider": "reference_openai_compatible",
      "base_url": "http://localhost:11434/v1",
      "token_rates": {
        "$include": "${env:CONFIG_DIR}/pricing/ollama.json"
      }
    }
  }
}
```

With `pricing/ollama.json` next to the config file:

```json
{
  "models": {
    "glm-5.2": {"input": 1.4, "cached": 0.26, "completion": 4.4}
  }
}
```

the resolved provider configuration contains the merged mapping:

```json
"token_rates": {
  "models": {
    "glm-5.2": {"input": 1.4, "cached": 0.26, "completion": 4.4}
  }
}
```

## Semantics

- Included content is the base; the object's local keys (other than
  `$include`) are the overlay, so local keys win on collision.
- Merging uses the same machinery as [mixins](configuration-mixins.md):
  a `$merge` directive on the included file's root governs the merge, else
  the including object's own `$merge`, else `mixin_policy.default_merge`
  (`shallow` by default).
- Includes are resolved after
  [placeholders](configuration-placeholders.md), so include paths support
  `${env:...}`, and before mixins, so included content may carry
  `mixin_refs`.
- Relative paths resolve against the directory of the file that carries the
  `$include` key; `~` expands to the user's home directory.

## Guards

Structured errors (same shape as mixin errors) are reported instead of
raising:

- `include_missing`: the referenced file does not exist; local keys are kept.
- `include_invalid`: unparsable JSON, a non-object file, or a non-string
  `$include` value.
- `include_cycle`: a file (transitively) includes itself; the cycle is cut.
- `include_depth_exceeded`: nesting exceeds `max_depth` (default `16`,
  matching mixin depth).

## Bundled pricing extracts

The bundled default config ships one-time pricing extracts under
`default_config/pricing/` (`ollama.json`, `zai.json`, `fireworks.json`) with
per-model token rates keyed by model id. The openai-compatible providers in
the default config include them via
`"token_rates": {"$include": "${env:CONFIG_DIR}/pricing/<provider>.json"}`,
and a first install copies them next to the installed config so the includes
resolve without manual steps. The files are manual snapshots of the
providers' official pricing pages (see each file's `_source` and
`_generated_at`); refresh them by re-extracting and committing.
