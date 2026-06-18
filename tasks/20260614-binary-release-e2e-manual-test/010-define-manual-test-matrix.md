# Define Manual Test Matrix

Define the exact platform, provider, plugin, and evidence matrix for the binary release end-to-end manual test.

## Requirements checklist

- [ ] Define supported platform coverage and installation method per platform.
- [ ] Select one real provider/API-key path for the LLM validation.
- [ ] Select one prompt or workflow that reliably causes a tool call.
- [ ] Select one custom user-side plugin that is not part of bundled plugins.
- [ ] Select one bundled plugin that is not part of the default config closure.
- [ ] Define pass/fail criteria and evidence to collect.
- [ ] Update this task with the final matrix before downstream testing begins.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

## Context

The release workflow currently builds these targets:

```text
linux-amd64
darwin-amd64
darwin-arm64
windows-amd64
```

The bash installer supports macOS/Linux targets only:

```text
darwin-amd64
darwin-arm64
linux-amd64
```

Windows currently uses the `.zip` asset directly. A PowerShell installer does not exist yet.

## Matrix To Define

For each platform, record:

```text
Platform:
Machine/provider:
Install method:
Artifact source:
Command shell:
Fresh user config location:
API provider:
API key env/config method:
Tool-call prompt:
Custom user plugin:
Bundled non-default plugin:
Expected evidence:
Tester:
Result:
Notes:
```

## Provider/API Key Selection

Pick exactly one provider path for this manual pass unless there is a strong reason to broaden it. The goal is to prove binary runtime behavior, not exhaustively test providers.

Selection criteria:

- available to testers without special local services
- supports tool calling in the current app/provider path
- already present or easy to enable from default config
- requires one API key
- produces deterministic enough behavior for a manual smoke prompt

Record the exact key name and setup command, for example:

```bash
export OPENAI_API_KEY="..."
```

or the equivalent config/auth step if the app expects it elsewhere.

## Plugin Selection

Pick:

1. A custom user-side plugin outside the release bundle.
   - Prefer a tiny test plugin in a temporary directory, or an existing plugin fixture copied outside the repo checkout.
   - The test must prove the installed binary can load/install plugins from user-owned paths without depending on the source checkout.

2. A bundled plugin not in the default config closure.
   - It should exist under the release package `plugins/` tree.
   - It should not be preinstalled as part of the default config closure.
   - The test should prove lazy installation or enabling from bundled plugin sources works.

Record the final choices here before `060-test-real-llm-tools-and-plugins.md` starts.

## Pass/Fail Criteria

A platform passes only if:

- the release artifact installs or extracts cleanly
- `crystal-lattice --help` succeeds
- `crystal-lattice --runtime-layout-json` reports `python-runtime`
- default config can be used without source-checkout paths
- one real LLM call succeeds
- one tool call is visible in terminal output, HTTP events, or session messages
- the selected custom user plugin is exercised
- the selected bundled non-default plugin is exercised
- cleanup steps are understood and documented
