# Plugin Docs And LLM Access

Include the current plugin documentation from `plugins/docs/` in the MkDocs site and generate LLM-accessible documentation files such as `llms.txt`.

## Requirements checklist

- [ ] Add `mkdocs-llmstxt` to `docs/requirements.txt`.
- [ ] Copy `plugins/docs/` into `docs/plugin-development/` during docs builds.
- [ ] Add copied plugin docs to the MkDocs nav.
- [ ] Configure MkDocs to emit `llms.txt`, and `llms-full.txt` if practical.
- [ ] Verify generated LLM files include overview, plugin docs, API reference, and tool host protocol content.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`

## Repo References

- `docs/requirements.txt:1-4` currently has MkDocs dependencies but no LLM docs plugin.
- `mkdocs.yml:14-29` currently configures `search` and `mkdocstrings`; add the LLM plugin alongside these.
- `mkdocs.yml:31-41` currently has Overview, Guides, and Reference nav sections; add a "Current Plugin Docs" section.
- `plugins/docs/index.md` is the current plugin docs entry point.
- `plugins/docs/` contains current plugin docs, including provider plugins, provider extensions, features, tools, actions, packaging/loading, execution order, config schema, UI elements, validation, and specialized task agents.

## Implementation Notes

Prefer a build preparation step instead of a symlink:

```bash
rm -rf docs/plugin-development
mkdir -p docs/plugin-development
rsync -a --delete plugins/docs/ docs/plugin-development/
```

This keeps CI and local builds predictable and makes existing relative links in `plugins/docs/index.md` more likely to resolve cleanly after copying.

Add a docs nav section similar to:

```yaml
  - Current Plugin Docs:
    - Start Here: plugin-development/index.md
    - Provider Plugins: plugin-development/provider-plugins.md
    - Provider Extensions: plugin-development/provider-extensions.md
    - Feature Plugins: plugin-development/feature-plugins.md
    - Application Plugins: plugin-development/application-plugins.md
    - Tool Plugins: plugin-development/tool-plugins.md
    - Tool Interop Flow: plugin-development/tool-interop.md
    - Node Tool Plugins: plugin-development/node-tool-plugins.md
    - Bash Tool Plugins: plugin-development/bash-tool-plugins.md
    - Plugin Actions: plugin-development/actions.md
    - Packaging And Loading: plugin-development/plugin-packaging-and-loading.md
    - Execution Order: plugin-development/plugin-execution-order.md
    - Configuration Schema: plugin-development/config-schema.md
    - UI Elements: plugin-development/ui-elements.md
    - Testing And Validation: plugin-development/testing-and-validation.md
    - Specialized Task Agents: plugin-development/specialized-task-agents.md
```

Add `mkdocs-llmstxt` to `docs/requirements.txt`:

```txt
mkdocs-llmstxt
```

Configure the plugin with a concise description and curated sections. Exact options should be checked against the installed plugin version, but the goal is:

- `/llms.txt`: compact navigable map for LLMs.
- `/llms-full.txt`: larger Markdown bundle if the plugin/config supports it cleanly.
- Include current plugin docs and generated mkdocstrings API reference.

Set `site_url` before relying on LLM docs output, because generated absolute links need the production docs URL.

## Validation

Run:

```bash
python -m pip install -r docs/requirements.txt
rm -rf docs/plugin-development
mkdir -p docs/plugin-development
rsync -a --delete plugins/docs/ docs/plugin-development/
mkdocs build --strict
```

Check generated files:

```bash
test -f site/llms.txt
```

If `llms-full.txt` is configured, also check:

```bash
test -f site/llms-full.txt
```

Manual checks:

- Plugin docs appear in MkDocs nav.
- Copied plugin docs have no broken relative links.
- `site/llms.txt` references core docs, plugin docs, API reference, and tool host protocol.
- The LLM docs output does not expose private-only deployment secrets or credentials.
