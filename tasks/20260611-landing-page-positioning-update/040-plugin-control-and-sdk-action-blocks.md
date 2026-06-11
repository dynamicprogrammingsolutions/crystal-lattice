# Plugin Control And SDK Action Blocks

Add small action-oriented sections that show how Crystal Lattice can be customized and automated, without turning the page into final docs.

## Requirements checklist

- [ ] Add or reuse a section type for non-numbered action blocks if `quickstart` is too limiting.
- [ ] Add a "Control with no compromises" section that shows config-driven, plugin-exposed settings.
- [ ] Add a "Build or replace a plugin" section with a prompt that asks the agent to inspect plugin docs and plan work.
- [ ] Add a Python automation section using actual simplified code after checking current APIs.
- [ ] Use a real-world CSV use case: generating personalized first LinkedIn messages.
- [ ] Investigate whether asking a plugin/agent to do batch processing for Codex is feasible and phrase accordingly.
- [ ] Prefer screenshots for session workbench and settings/plugin UI examples where possible.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`
Depends On: `tasks/20260611-landing-page-positioning-update/020-homepage-structure-and-copy.md`

## Files To Inspect

Landing page:

- `landing_page/src/components/Quickstart.astro`
- `landing_page/src/section-system/registry.ts`
- `landing_page/src/content/pages/home.yaml`

Main platform code/docs for accurate snippets:

- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`
- `plugins/docs/index.md`
- `plugins/docs/tool-plugins.md`
- `plugins/docs/application-plugins.md`
- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`
- `plugins/docs/ui-elements.md`
- `plugins/docs/plugin-packaging-and-loading.md`
- User's `HOME/.crystal/config.json` or relevant config example for plugin-exposed temperature, if available and safe to inspect.

## Section Type Recommendation

Minimal option:

- Reuse `quickstart` for all action blocks.

Better small option:

- Add `ActionBlocks.astro` with:
  - `eyebrow`
  - `title`
  - `body`
  - `blocks[]`
  - block fields: `title`, `body`, `code`, optional `caption`

This avoids forcing every action block into numbered quickstart steps.

## Draft Control Section

Title:

```text
Control with no compromises
```

Body:

```text
Serious users eventually disagree with the defaults. In Crystal Lattice, a setting can exist because a plugin exposes it, and that plugin can be replaced.
```

Illustration target:

```text
Show a config snippet plus screenshot for a request option exposed by a plugin, for example temperature from the user's HOME/.crystal config. The exact snippet should be taken from a real config or sanitized real config.
```

Draft explanation:

```text
The app does not need to know every possible provider option ahead of time. A plugin describes the setting, the UI renders it, and the request pipeline applies it.
```

## Draft Plugin Planning Prompt

```text
I want to build a Crystal Lattice plugin.

Please inspect the plugin documentation in this repository, especially:
- plugins/docs/index.md
- plugins/docs/tool-plugins.md
- plugins/docs/application-plugins.md
- plugins/docs/provider-plugins.md
- plugins/docs/provider-extensions.md
- plugins/docs/ui-elements.md
- plugins/docs/plugin-packaging-and-loading.md

Goal:
Create a plugin that [describe what I want].

Please:
1. Identify whether this should be a provider, provider extension, feature, tool, or application plugin.
2. Find the closest existing plugin to copy from.
3. Explain what UI, if any, the plugin should expose.
4. Propose the file layout.
5. Draft an implementation plan.
6. Tell me what tests should be added before coding.
```

Config snippet:

```json
{
  "plugins": [
    "path:./plugins/my-custom-plugin"
  ]
}
```

## Draft Python Automation Section

Title:

```text
Automate the same harness with Python
```

Body:

```text
Use Crystal Lattice from scripts when the job is repetitive: CSV enrichment, evaluations, internal tools, or batch drafting. The script can use the same configured agents and plugins as the app UI.
```

Use case:

```text
Generate personalized first LinkedIn messages from a CSV of leads.
```

Target code shape, to be corrected against the actual API before publishing:

```python
import csv
from pathlib import Path

from agent_app import AgentApplication

app = AgentApplication.from_config("./.crystal/config.json")

with Path("leads.csv").open(newline="") as input_file, Path("messages.csv").open("w", newline="") as output_file:
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(output_file, fieldnames=["name", "company", "message"])
    writer.writeheader()

    for lead in reader:
        session = app.create_session(agent_id="codex-openrouter")
        prompt = (
            "Write a concise, friendly first LinkedIn message. "
            "Use the lead details, avoid hype, and do not invent facts.\n\n"
            f"Name: {lead['name']}\n"
            f"Role: {lead.get('role', '')}\n"
            f"Company: {lead.get('company', '')}\n"
            f"Notes: {lead.get('notes', '')}"
        )

        app.add_message(session.session_id, "user", prompt)
        result = app.send_request(session.session_id, stream=False)

        writer.writerow({
            "name": lead["name"],
            "company": lead.get("company", ""),
            "message": result.final_text,
        })
```

Important: this is a draft shape. The implementer must verify the actual public API before landing the code.

## Batch Processing Feasibility Check

Investigate whether there is a realistic plugin or agent pattern for batch processing with Codex-style agents:

- If feasible now, include a small prompt/action block.
- If not clearly feasible, only mention Python automation and defer a batch plugin section.
