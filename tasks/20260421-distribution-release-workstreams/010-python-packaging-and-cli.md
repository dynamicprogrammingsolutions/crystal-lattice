# Python Packaging And CLI

Prepare the Python packages for end-user installation and establish one stable command that every release channel can target.

## Requirements checklist

- [ ] Align `agent-core` and `agent-terminal-app` versioning strategy for releases.
- [ ] Add a supported CLI entrypoint for `agent-terminal-app` via packaging metadata.
- [ ] Confirm and document the intended user-facing invocation for source, venv, and `pipx` installs.
- [ ] Capture any packaging/documentation updates needed to support downstream binary and installer work.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

## Current state

- `core/python/pyproject.toml:5-43` already defines the `agent-core` package at version `0.3.0`.
- `application/python/pyproject.toml:5-26` already defines the `agent-terminal-app` package at version `0.1.0` and depends on `agent-core>=0.3.0`.
- `application/python/pyproject.toml:5-26` does not currently define a `[project.scripts]` entry for an `agent-terminal-app` command.
- The current operational entrypoint is `python -m agent_terminal_app`, which is functional but less convenient than a packaged console script.

## Proposed solution from conversation

- Add a first-class console script in `application/python/pyproject.toml`, for example:

  ```toml
  [project.scripts]
  agent-terminal-app = "agent_terminal_app.__main__:main"
  ```

- Ensure `agent_terminal_app/__main__.py` exposes a `main()` function that matches the existing `python -m agent_terminal_app` behavior.
- Keep PyPI distribution available for users with compatible Python, and recommend `pipx install agent-terminal-app` as the cleanest Python-native install path.
- Treat this CLI name as the canonical command referenced by GitHub Releases, the `curl` installer, Homebrew, and any npm wrapper.

## Deliverables

- Packaging metadata changes for the console script.
- Release notes / docs updates covering `pip install`, `pipx install`, and direct module invocation.
- A short note on version bump policy between `agent-core` and `agent-terminal-app`.