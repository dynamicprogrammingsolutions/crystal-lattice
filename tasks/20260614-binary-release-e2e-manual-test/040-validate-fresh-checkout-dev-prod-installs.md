# Validate Fresh Checkout Dev And Prod Installs

Validate that a developer can start from a fresh repository checkout and successfully run both the dev install flow and local production/binary install rehearsal.

## Requirements checklist

- [ ] Create a fresh clone or clean checkout in a temporary location.
- [ ] Run source/dev install commands.
- [ ] Verify the dev `crystal-lattice` command works.
- [ ] Run `nox -s install_dev_local` if in scope for developer UX.
- [ ] Run bundled-Python package build from the fresh checkout.
- [ ] Run local production install rehearsal from the generated archive.
- [ ] Verify installed prod command reports `python-runtime`.
- [ ] Record prerequisites, failures, confusing output, and elapsed time notes.
- [ ] Identify small README/doc improvements.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On: `tasks/20260614-binary-release-e2e-manual-test/020-prepare-manual-test-commands.md`

## Context

Local maintainer commands are defined in `noxfile.py`:

```bash
nox -s build_bundle
nox -s build_optimized_bundle
nox -s install_prod_local
nox -s install_dev_local
```

`build_bundle` and `install_prod_local` are documented as the release-shaped local path:

1. install local build dependencies
2. run `scripts/build_crystal_lattice_python_runtime_package.py`
3. smoke-test the generated release archive
4. install from the archive
5. link `crystal-lattice` into `~/.local/bin`

## Fresh Checkout Flow

Prepare and run a clean clone flow similar to:

```bash
WORKDIR="$(mktemp -d)"
git clone <repo-url> "$WORKDIR/ai-agent-platform"
cd "$WORKDIR/ai-agent-platform"
```

If testing local unmerged changes, document whether the checkout is:

- a branch pushed to origin
- a local clone from the current worktree
- a clean git archive/snapshot

## Dev Install Commands

Validate the documented source install:

```bash
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
crystal-lattice --help
crystal-lattice --runtime-layout-json
```

Optionally validate the dev command helper:

```bash
python -m pip install nox
nox -s install_dev_local
~/.local/bin/crystal-lattice-cli-dev --help
```

## Prod/Binary Rehearsal Commands

Validate:

```bash
python -m pip install nox
nox -s build_bundle
nox -s install_prod_local
~/.local/bin/crystal-lattice --help
~/.local/bin/crystal-lattice --runtime-layout-json
```

If testing must not touch the developer's normal `~/.local/bin`, prepare an alternate command using `scripts/install_crystal_lattice_archive.py` directly:

```bash
INSTALL_ROOT="$(mktemp -d)/opt/crystal-lattice-cli"
BIN_DIR="$(mktemp -d)/bin"

python scripts/install_crystal_lattice_archive.py \
  --install-root "$INSTALL_ROOT" \
  --bin-dir "$BIN_DIR"

"$BIN_DIR/crystal-lattice" --runtime-layout-json
```

## UX Notes To Collect

Record:

- missing system prerequisites
- Python version issues
- confusing package install output
- whether commands are easy to discover
- whether docs explain where generated artifacts land
- whether cleanup is clear
- whether source and prod commands conflict on `PATH`
