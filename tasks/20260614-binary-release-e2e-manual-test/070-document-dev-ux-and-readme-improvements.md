# Document Developer UX And README Improvements

Apply small documentation improvements discovered while preparing and running the binary release end-to-end manual test.

## Requirements checklist

- [ ] Review UX notes from command preparation.
- [ ] Review UX notes from fresh checkout dev/prod install validation.
- [ ] Review UX notes from platform artifact testing.
- [ ] Review UX notes from real LLM/tool/plugin testing.
- [ ] Update README/docs where small changes reduce release-test friction.
- [ ] Correct the pinned install command if still needed.
- [ ] Add or refine custom-domain installer guidance if useful.
- [ ] Add or refine manual release verification checklist if useful.
- [ ] Add or refine Windows archive install notes if useful.
- [ ] Keep documentation changes focused and lightweight.
- [ ] Run relevant doc/test checks if docs include executable commands.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On:

- `tasks/20260614-binary-release-e2e-manual-test/020-prepare-manual-test-commands.md`
- `tasks/20260614-binary-release-e2e-manual-test/040-validate-fresh-checkout-dev-prod-installs.md`
- `tasks/20260614-binary-release-e2e-manual-test/050-test-release-artifacts-on-all-platforms.md`
- `tasks/20260614-binary-release-e2e-manual-test/060-test-real-llm-tools-and-plugins.md`

## Context

Current likely doc targets:

- `README.md`
- `application/python/README.md`

The relevant current docs include:

- install command near the top-level README quickstart
- `application/python/README.md` installation section
- `application/python/README.md` release and distribution section
- `application/python/README.md` local nox scripts section
- `application/python/README.md` GitHub Release workflow section

## Known Potential Improvement

The current pinned install example should be checked. In a pipeline, this shape is reliable because `VERSION` is available to the `bash` process:

```bash
curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | VERSION="0.1.0" bash
```

or, with the custom domain override:

```bash
curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | \
  VERSION="0.1.0" \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL" \
  bash
```

Avoid documenting this shape for pinned installs:

```bash
VERSION="0.1.0" curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | bash
```

That only sets `VERSION` for `curl`, not for the `bash` process running the installer.

## Documentation Scope

Make small, practical changes only. This task is not a broad rewrite.

Good changes include:

- one concise manual release verification checklist
- corrected install command examples
- one custom-domain install example
- clearer fresh checkout dev/prod install commands
- clear note that Windows currently uses the `.zip` archive
- clearer note that custom domains must serve `install.sh`, `latest.txt`, and archives from the same URL base

Avoid:

- large release-process redesigns
- unrelated architecture documentation
- speculative automation not exercised by the manual test

## Verification

At minimum:

```bash
rg -n "install.sh|VERSION=|CRYSTAL_LATTICE_DOWNLOAD_BASE_URL|release" README.md application/python/README.md
```

If commands or generated examples are changed, run the narrowest relevant tests or command smoke checks and record them in completion notes.
