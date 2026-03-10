# Verbosity Extension Responses API

Short description: Implement verbosity control in `openai_responses_verbosity` extension with model-gated tags and request payload shaping.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Implementation

1. Implement verbosity config schema/UI.
2. Gate extension by capability tags (for example `supports_verbosity`).
3. Inject verbosity into request payload shape expected by Responses API.
4. Keep verbosity logic extension-only.

## Tests (required in this step)

1. Unit tests for init and request mutation behavior.
2. Unit tests for no-op behavior when verbosity is unset/invalid.
3. Unit tests for tag-gated visibility/activation.
4. Integration smoke test with verbosity set.

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_verbosity_extension.py`
- `plugins/openrouter_responses/tests/test_openrouter_verbosity_extension_unit.py`
- `plugins/openrouter_responses/tests/test_openrouter_verbosity_integration.py`
