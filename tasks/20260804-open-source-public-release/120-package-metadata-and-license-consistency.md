# Normalize Package Metadata And Repository-Wide License Signals

Improve package-manager and distribution metadata after publication without
blocking the initial source release.

## Requirements checklist

- [ ] First-party distributable packages declare accurate license metadata and project URLs.
- [ ] Subtree licenses and package metadata agree with root licensing rules.
- [ ] Third-party attribution and notice boundaries are understandable for packaged artifacts.
- [ ] Templates teach new plugin authors to include correct license metadata.
- [ ] Generated package metadata does not claim a license broader than the files included in the package.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md

## Known starting state

Many first-party `pyproject.toml` files do not declare a PEP 621 `license` field
or license classifiers. A smaller number of `package.json` files lack a
`license` field. Root and many subtree license files already exist.

Claude Tools itself is handled before publication in task `020`; this task
normalizes the remaining repository.

## Execution plan
Status: Draft

Inventory only packages intended for build, installation, or publication;
exclude test-only fixtures from mandatory metadata. Add SPDX-compatible license
metadata, repository/homepage/issues URLs, and classifiers where appropriate.
Validate built wheel/sdist/npm contents and included license files.

Update plugin templates so future packages inherit correct metadata.

### Implementation decisions and open questions

- Test-only fixture packages do not need full publication metadata.
- Do not add subtree `LICENSE` files mechanically when root inheritance is
  clearer and packaging does not require a copy.

### Documentation

- Update package-authoring documentation and templates.

### Task checklist

- [ ] Identify distributable packages.
- [ ] Normalize Python package metadata.
- [ ] Normalize Node package metadata.
- [ ] Validate built artifact license inclusion.
- [ ] Update templates and authoring docs.

### Requirement verification

- Package metadata checks report no missing license/project fields for
  distributable first-party packages.
- Sample built artifacts contain the expected license and notice files.
