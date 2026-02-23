# Follow-up: Auto-detect plugin runtime for `path:` / `git+` repo specs

## Description

Today, repo specs use:

- Local repo: `"path:/abs/or/rel"`
- Git repo: `"git+<url-or-local>[#ref]"`

and are assumed to be **Python** plugin repositories (pip-installed into `plugin_cache_dir`, then loaded via `agent_plugin.json` `entries`).

This follow-up task adds an **auto-detection layer** so that the same repo spec formats (`path:` and `git+`) can resolve to:

- **Python** plugin repos (existing behavior)
- **Bash tool** repos (new; descriptor-driven, copy-only)
- **Node.js (JS/TS) tool** repos (new; descriptor-driven via `package.json`, copy-only with optional install/build)

This must be decided **before any install step**.

---

## Goal

- Allow users to specify repos with `path:` / `git+` without caring about runtime.
- Detect runtime based on repository files:
  - Bash: presence of `agent_plugin.json` with `bash_tools`.
  - JS/TS: presence of `package.json` (and `package.json#agent.tools` for tool plugins).
  - Python: default when `agent_plugin.json` has `entries` and project is pip-installable.

---

## Proposed detection rules

### Inputs

- A **local directory** (from `path:`)
- A **checked-out git working tree** (from `git+`; requires clone/checkout to temp)

### Rule ordering

1) **Bash tool repo**
   - If `agent_plugin.json` exists and includes a non-empty `bash_tools` array.
2) **Node.js tool repo**
   - Else, if `package.json` exists.
   - Must validate that `package.json#agent.tools` exists and is non-empty when resolving as a tool plugin.
3) **Python plugin repo**
   - Else, treat as Python:
     - `agent_plugin.json` has non-empty `entries`.
     - Repo contains `pyproject.toml` or `setup.py`.

Ambiguity handling:

- If both `bash_tools` and `entries` are present in `agent_plugin.json`, fail with a clear error.
- If both `agent_plugin.json` (bash_tools) and `package.json` exist, prefer bash_tools (explicit).

---

## Implementation plan

### 1) Descriptor parsing

Extend descriptor reading to support:

- Python descriptor fields (existing):
  - `entries: ["pkg.module.Class", ...]`
- Bash descriptor fields (new):
  - `bash_tools: [{"file": "tools/my_tool.bash"}, ...]`

Implementation options:

- Add a new reader `read_descriptor_any(...)` returning a tagged union.
- Or extend `read_descriptor(...)` to return both `entries` and `bash_tools` (and validate ambiguity).

### 2) New “auto repo” sources (recommended approach)

Add two new plugin sources that exclusively handle the existing repo string forms:

- `AutoPathRepoSource` supports `"path:..."`.
- `AutoGitRepoSource` supports `"git+..."`.

They:

1) Resolve the directory (or clone/checkout to temp).
2) Detect runtime using the rules above.
3) Delegate to the appropriate underlying source:
   - Python → existing `LocalPathRepoSource` / `GitRepoSource` behavior.
   - Bash → new `BashToolSource` directory/git resolver (copy-only).
   - Node → existing `NodeToolSource` directory/git resolver (copy-only + optional install/build).

Important: ensure delegation still respects policy and caching semantics.

### 3) Update PluginManager default sources

Today, `DottedClassSource` ignores strings starting with `path:` or `git+`.

Update default ordering so the auto sources claim these first:

1) `DottedClassSource` (dotted strings)
2) `AutoPathRepoSource` (path:...)
3) `AutoGitRepoSource` (git+...)
4) (Optional) leave explicit sources available for dict forms:
   - `BashToolSource` (`{ "bash_tool": ... }`)
   - `NodeToolSource` (`{ "node_tool": ... }`)
   - `LocalPathRepoSource` (dict forms)
   - `GitRepoSource` (dict forms)

### 4) Security/policy considerations

- Git repos still require `plugin_policy.allow_remote` for remote URLs.
- Add new policy keys:
  - `plugin_policy.allow_bash_tools` (default false)
  - `plugin_policy.allow_node_tools` (default true or false; decide)

Auto-detection must fail fast if:

- The repo is detected as bash/node but the corresponding allow policy is disabled.

### 5) Tests

Add tests that exercise `path:` and `git+` with three fixtures:

- Python plugin repo fixture (existing patterns)
- Bash repo fixture (`agent_plugin.json` with `bash_tools` + scripts)
- Node repo fixture (`package.json` with `agent.tools`)

Assertions:

- Detection selects the correct runtime.
- Bash/node repos are not pip-installed.
- Python repos are pip-installed.
- Errors are clear for ambiguous descriptors.

### 6) Docs

- Update `docs/plugins/application-config.md` to explain that `path:` and `git+` can resolve to Python/bash/node, and list detection rules.

---

## Caveats

- This changes the meaning of `path:` and `git+` by adding additional runtimes; ensure backward compatibility by making Python the default when in doubt.
- JS detection by `package.json` alone may match repos that are not intended as Node tool plugins; require `package.json#agent.tools` for resolution to avoid surprising behavior.
