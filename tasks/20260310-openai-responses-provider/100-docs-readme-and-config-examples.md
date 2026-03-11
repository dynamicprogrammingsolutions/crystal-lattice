# Docs README And Config Examples

Short description: Document the new `openai_responses` plugin bundle, its extension-centric design, configuration, and test execution workflow.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Implementation

1. Write plugin README with:
- quickstart config examples
- extension list and ownership boundaries (tools/reasoning/usage/verbosity)
- required environment variables
- troubleshooting notes
 - explicit note that local integration tests use `OPENAI_API_KEY` from repo root `.env`
2. Update relevant docs index/navigation as needed.
3. Document test commands and markers.

## Validation

1. Run plugin unit tests.
2. Run at least one integration smoke test path (when credentials are present).
3. Ensure documented class paths and config snippets match actual package names.

## References

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`
- `plugins/docs/testing-and-validation.md`
- `plugins/openrouter_responses/README.md`
