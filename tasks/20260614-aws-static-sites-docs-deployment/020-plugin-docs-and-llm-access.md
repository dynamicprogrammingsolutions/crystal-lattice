# Plugin Docs And LLM Access

Include the current plugin documentation from `plugins/docs/` in the MkDocs site and generate LLM-accessible documentation files such as `llms.txt`.

## Requirements checklist

- [x] Add `mkdocs-llmstxt` to `docs/requirements.txt`.
- [x] Copy `plugins/docs/` into `docs/plugin-development/` during docs builds.
- [x] Generate docs-local pages for built-in plugin README files.
- [x] Generate a Markdown default-config reference page that wraps the default JSON config in a fenced code block.
- [x] Update existing docs links so built-in plugin README references and default config references point to generated docs-local pages.
- [x] Add copied plugin docs to the MkDocs nav.
- [x] Configure MkDocs to emit `llms.txt`, and `llms-full.txt` if practical.
- [x] Verify generated LLM files include overview, plugin docs, API reference, and tool host protocol content.

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

## Execution plan

Added during completion after user approval.

This task will add a repeatable MkDocs preparation step under `docs_site/`, then configure MkDocs to publish generated plugin documentation and LLM-accessible docs files.

Execution approach:

1. Add a docs-site support script at `docs_site/scripts/prepare_mkdocs_site.py`. Keep the script under `docs_site/` because it is implementation/support machinery, while generated publishable content belongs under `docs/`.
2. Have the script delete and regenerate `docs/plugin-development/` from `plugins/docs/`, excluding internal support files such as `AGENTS.md` and normalizing repo-root-style links where needed.
3. Have the script delete and regenerate `docs/built-in-plugins/` from every `plugins/*/README.md`, with one page per plugin at `docs/built-in-plugins/<plugin-name>/index.md` and a generated index at `docs/built-in-plugins/index.md`.
4. Have the script generate `docs/reference/default-config.md` from `application/python/agent_terminal_app/default_config/config.json`, wrapping the full JSON in a fenced `json` code block.
5. Add the generated docs paths to `.gitignore` so source-of-truth content remains in `plugins/docs/`, `plugins/*/README.md`, and the default config JSON.
6. Update `docs_site/README.md` to document the preparation step before local and CI MkDocs builds.
7. Add `mkdocs-llmstxt` to `docs/requirements.txt`.
8. Update `mkdocs.yml` to include the LLM docs plugin, emit `llms.txt` and `llms-full.txt` if supported cleanly, and add nav sections for current plugin docs, built-in plugin docs, and the generated default configuration reference.
9. Update broken repo-root-style links in `docs/plugins/application-config.md` so they point to generated docs-local pages.
10. Validate by running the prep script, installing docs requirements if needed, building MkDocs, checking `site/llms.txt` and `site/llms-full.txt`, and attempting `mkdocs build --strict`. If strict mode still fails only on pre-existing cleanup or mkdocstrings warnings, record those separately in completion notes.

## Completion Notes

Added during completion.

Implemented the docs generation and LLM-access pass:

- Added `docs_site/scripts/prepare_mkdocs_site.py` as the repeatable docs preparation step.
- The preparation script generates `docs/plugin-development/` from `plugins/docs/`, excluding `AGENTS.md` and normalizing the known copied-doc links/anchors.
- The preparation script generates `docs/built-in-plugins/<plugin-name>/index.md` for every `plugins/*/README.md`, plus `docs/built-in-plugins/index.md`.
- The preparation script generates `docs/reference/default-config.md` from `application/python/agent_terminal_app/default_config/config.json` in a fenced `json` block.
- Added generated docs paths to `.gitignore`.
- Documented the prep step in `docs_site/README.md`.
- Added `mkdocs-llmstxt` to `docs/requirements.txt`.
- Configured `mkdocs.yml` to emit `llms.txt` and `llms-full.txt`, include curated LLM sections, and publish nav entries for current plugin docs, built-in plugin README pages, and the generated default configuration reference.
- Updated `docs/plugins/application-config.md` links so built-in plugin README references and default config references point to docs-local generated pages.
- Follow-up LLM accessibility UI added after the initial task completion: `docs_site/overrides/partials/actions.html` adds a page-level dropdown for copying the current page as Markdown, opening the current page Markdown, opening `llms.txt`, and opening `llms-full.txt`; `docs/assets/javascripts/llm-actions.js` implements the client behavior.
- Follow-up AWS deployment note added to `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`: production docs deploys should upload `site/**/*.md`, `site/llms.txt`, and `site/llms-full.txt` with `Content-Type: text/plain; charset=utf-8` so Markdown/LLM text files open inline in browsers.
- Follow-up Safari copy fix added after testing the reported `NotAllowedError`: `docs/assets/javascripts/llm-actions.js` now preloads page Markdown, copies only cached Markdown during the click handler, shows `Loading...`/`Ready` if content is not ready yet, and falls back to a hidden textarea plus `document.execCommand("copy")` if the Clipboard API rejects the write.

Validation performed:

- `python docs_site/scripts/prepare_mkdocs_site.py` succeeded.
- `python -m pip install -r docs/requirements.txt` succeeded; dependencies were already installed, including `mkdocs-llmstxt 0.5.0`.
- `mkdocs build` succeeded.
- `test -f site/llms.txt` and `test -f site/llms-full.txt` succeeded.
- Confirmed `site/llms.txt` references overview, current plugin docs, built-in plugin docs, API reference, tool host protocol, and default configuration content.
- Ran a targeted secret-pattern scan over `site/llms.txt` and `site/llms-full.txt`; it found no AWS keys, private keys, OpenAI-style `sk-` tokens, GitHub tokens, or Slack tokens. The generated content still includes placeholder environment variable names such as `OPENAI_API_KEY`, as expected.
- `mkdocs build --strict` was attempted and still fails only on four pre-existing strict warnings from `mkdocstrings`/`mkdocs_autorefs`: three griffe indentation warnings in `core/python/agent_core/core.py` around line 2991 and one unresolved cross-reference target for `"content"`. The old omitted-docs-tree messages remain informational and are tracked by `tasks/20260614-aws-static-sites-docs-deployment/025-docs-content-cleanup.md`.
