# Python Packaging And CLI

Prepare the Python packages for end-user installation and establish one stable command that every release channel can target.

## Requirements checklist

- [x] Align `agent-core` and `crystal-lattice-cli` versioning strategy for releases.
- [x] Rename the installable terminal application distribution to `crystal-lattice-cli`.
- [x] Add a supported `crystal-lattice` CLI entrypoint via packaging metadata.
- [x] Confirm and document the intended user-facing invocation for source, venv, and `pipx` installs.
- [x] Capture any packaging/documentation updates needed to support downstream binary and installer work.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

## Initial state

- `core/python/pyproject.toml:5-43` already defines the `agent-core` package at version `0.3.0`.
- `application/python/pyproject.toml:5-26` already defines the `agent-terminal-app` package at version `0.1.0` and depends on `agent-core>=0.3.0`.
- `application/python/pyproject.toml:5-26` does not currently define a `[project.scripts]` entry for an `agent-terminal-app` command.
- The current operational entrypoint is `python -m agent_terminal_app`, which is functional but less convenient than a packaged console script.

## Proposed solution from conversation

- Rename the installable Python distribution from `agent-terminal-app` to `crystal-lattice-cli`, while keeping the internal Python package/module directory named `agent_terminal_app`.
- Add a first-class console script in `application/python/pyproject.toml`, using `crystal-lattice` as the canonical terminal command:

  ```toml
  [project.scripts]
  crystal-lattice = "agent_terminal_app.__main__:main"
  ```

- Ensure `agent_terminal_app/__main__.py` exposes a `main()` function that matches the existing `python -m agent_terminal_app` behavior.
- Keep PyPI distribution available for users with compatible Python, and recommend `pipx install crystal-lattice-cli` as the cleanest Python-native install path.
- Treat this CLI name as the canonical command referenced by GitHub Releases, the `curl` installer, Homebrew, and any npm wrapper.

## Deliverables

- Packaging metadata changes for the console script.
- Release notes / docs updates covering `pip install`, `pipx install`, and direct module invocation.
- A short note on version bump policy between `agent-core` and `crystal-lattice-cli`.

## Execution plan

Added during completion.

1. Update `application/python/pyproject.toml` so the installable distribution is `crystal-lattice-cli`, includes package README metadata, and exposes `crystal-lattice = "agent_terminal_app.__main__:main"`.
2. Keep `agent_terminal_app.__main__:main` as the single runtime entrypoint for both `crystal-lattice` and `python -m agent_terminal_app`.
3. Update `application/python/README.md` and relevant root `README.md` examples so end users install with `pipx install crystal-lattice-cli` or `pip install crystal-lattice-cli`, then run `crystal-lattice`.
4. Document the release/versioning policy: `agent-core` and `crystal-lattice-cli` version independently, and the CLI package raises its `agent-core` dependency floor when it needs newer core behavior.
5. Add a lightweight packaging metadata regression test for the distribution name and console script.
6. Verify with focused tests and command help checks where the local environment permits.

## Completion Notes

Added during completion.

- Renamed the installable terminal application distribution to `crystal-lattice-cli` in `application/python/pyproject.toml`.
- Added the canonical console script `crystal-lattice = "agent_terminal_app.__main__:main"` while keeping `agent_terminal_app` as the internal module and `python -m agent_terminal_app` as a supported developer/debugging path.
- Added package README metadata for future PyPI publishing.
- Updated `application/python/README.md` and relevant root `README.md` examples to document `pipx install crystal-lattice-cli`, `pip install crystal-lattice-cli`, and the `crystal-lattice` command.
- Documented independent `agent-core` / `crystal-lattice-cli` versioning and the policy for bumping the CLI dependency floor when newer core behavior is required.
- Added `application/python/tests/test_packaging_metadata.py` to guard the distribution name and console script metadata.
- Updated downstream handoff notes so binary, CI, curl, Homebrew, and npm tasks target `crystal-lattice-cli` release artifacts and the `crystal-lattice` executable.
- Verified `pytest application/python/tests/test_packaging_metadata.py -q`, `python -m agent_terminal_app --help`, and `crystal-lattice --help` after a local editable install with `python -m pip install -e application/python --no-deps`.