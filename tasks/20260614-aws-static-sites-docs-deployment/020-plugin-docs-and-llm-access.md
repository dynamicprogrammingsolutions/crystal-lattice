# Plugin Docs And LLM Access

Include the current plugin documentation from `plugins/docs/` in the MkDocs site and generate LLM-accessible documentation files such as `llms.txt`.

## Requirements checklist

- [ ] Add `mkdocs-llmstxt` to `docs/requirements.txt`.
- [ ] Copy `plugins/docs/` into `docs/plugin-development/` during docs builds.
- [ ] Generate docs-local pages for built-in plugin README files.
- [ ] Generate a Markdown default-config reference page that wraps the default JSON config in a fenced code block.
- [ ] Update existing docs links so built-in plugin README references and default config references point to generated docs-local pages.
- [ ] Add copied plugin docs to the MkDocs nav.
- [ ] Configure MkDocs to emit `llms.txt`, and `llms-full.txt` if practical.
- [ ] Verify generated LLM files include overview, plugin docs, API reference, and tool host protocol content.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`

Related Follow-Up: `tasks/20260614-aws-static-sites-docs-deployment/025-docs-content-cleanup.md`

## Repo References

- `docs/requirements.txt:1-4` currently has MkDocs dependencies but no LLM docs plugin.
- `mkdocs.yml:14-29` currently configures `search` and `mkdocstrings`; add the LLM plugin alongside these.
- `mkdocs.yml:31-41` currently has Overview, Guides, and Reference nav sections; add a "Current Plugin Docs" section.
- `plugins/docs/index.md` is the current plugin docs entry point.
- `plugins/docs/` contains current plugin docs, including provider plugins, provider extensions, features, tools, actions, packaging/loading, execution order, config schema, UI elements, validation, and specialized task agents.
- `plugins/*/README.md` contains built-in plugin README files that should be available from the docs site through generated docs-local pages.
- `application/python/agent_terminal_app/default_config/config.json` is the default config source. Generate a Markdown docs page that presents this JSON in a fenced `json` code block instead of linking to the raw repo file.
- `docs/plugins/application-config.md` currently has repo-root-style links to `application/python/agent_terminal_app/default_config/config.json` and `plugins/feature-system-message/README.md`; these should be rewritten to generated docs-local pages during this task.
- `docs/index.md` and obsolete docs-tree content cleanup are tracked separately in `tasks/20260614-aws-static-sites-docs-deployment/025-docs-content-cleanup.md`.

## Implementation Notes

Prefer a build preparation step instead of a symlink:

```bash
rm -rf docs/plugin-development
mkdir -p docs/plugin-development
rsync -a --delete plugins/docs/ docs/plugin-development/
```

This keeps CI and local builds predictable and makes existing relative links in `plugins/docs/index.md` more likely to resolve cleanly after copying.

Extend the same build preparation idea for generated docs-local references.

Built-in plugin READMEs:

- Read `plugins/*/README.md`.
- Generate one MkDocs page per plugin under a docs-local directory, for example `docs/built-in-plugins/<plugin-name>/index.md`.
- Preserve the README content where practical, but prepend a small generated source note if useful.
- Generate `docs/built-in-plugins/index.md` as an index of all generated built-in plugin README pages.
- Add the built-in plugin index to MkDocs nav.

Default config reference:

- Read `application/python/agent_terminal_app/default_config/config.json`.
- Generate a Markdown page, for example `docs/reference/default-config.md`.
- Include a short intro and wrap the full JSON in a fenced code block:

````md
# Default Configuration

Generated from `application/python/agent_terminal_app/default_config/config.json`.

```json
{
  "...": "..."
}
```
````

Do not link directly from MkDocs pages to repo-root files unless those links are full GitHub URLs. Prefer docs-local pages for content that should be browseable in the published documentation site.

After generating those pages, update broken repo-root-style links in `docs/plugins/application-config.md`:

- Replace `application/python/agent_terminal_app/default_config/config.json` with a link to the generated default config page, likely `../reference/default-config.md`.
- Replace `plugins/feature-system-message/README.md` with a link to the generated built-in plugin page, likely `../built-in-plugins/feature-system-message/`.

Also update the "See Also" section in `docs/plugins/application-config.md` so built-in plugin README references point to generated docs-local pages such as `../built-in-plugins/codex-tools/`, `../built-in-plugins/gemini-tools/`, `../built-in-plugins/qwen-tools/`, and `../built-in-plugins/grok-tools/`.

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
  - Built-In Plugins:
    - Index: built-in-plugins/index.md
  - Reference:
    - Default Configuration: reference/default-config.md
```

Add `mkdocs-llmstxt` to `docs/requirements.txt`:

```txt
mkdocs-llmstxt
```

Configure the plugin with a concise description and curated sections. Exact options should be checked against the installed plugin version, but the goal is:

- `/llms.txt`: compact navigable map for LLMs.
- `/llms-full.txt`: larger Markdown bundle if the plugin/config supports it cleanly.
- Include current plugin docs and generated mkdocstrings API reference.
- Include the generated built-in plugin README pages and generated default configuration page where practical.

Set `site_url` before relying on LLM docs output, because generated absolute links need the deployed docs URL. During the testing phase, use `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/`; switch to `https://docs.crystallattice.dev/` only when the final domain cutover happens.

## Validation

Run:

```bash
python -m pip install -r docs/requirements.txt
rm -rf docs/plugin-development
mkdir -p docs/plugin-development
rsync -a --delete plugins/docs/ docs/plugin-development/
# Generate docs/built-in-plugins/** from plugins/*/README.md.
# Generate docs/reference/default-config.md from application/python/agent_terminal_app/default_config/config.json.
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
- Built-in plugin README pages appear in MkDocs nav or at least through a docs-local index page.
- The generated default config page renders as Markdown with a fenced JSON code block.
- Copied plugin docs have no broken relative links.
- Links in `docs/plugins/application-config.md` no longer point to repo-root-relative paths that MkDocs resolves as broken docs-local links.
- `site/llms.txt` references core docs, plugin docs, API reference, and tool host protocol.
- The LLM docs output does not expose private-only deployment secrets or credentials.
