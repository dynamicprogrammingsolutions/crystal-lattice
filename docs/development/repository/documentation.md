# Crystal Lattice documentation policy

This page maps the [reusable documentation standard](../standards/documentation.md)
to Crystal Lattice paths, packages, shared documentation domains, site
assembly, and migration.

## Source structure

Public/reusable packages, applications, SDKs, and services target:

```text
<package>/
├── README.md
├── AGENTS.md
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── ...
    ├── development/
    │   ├── index.md
    │   ├── ...
    │   └── specifications/
    └── reference/              # optional/generated
```

Small plugins and internal packages may remain README-only when inherited
guidance and that README provide a complete route. Do not add empty AGENTS,
index, or quickstart pages.

Repository-wide output is organized as:

```text
docs/development/
├── index.md
├── standards/                  # reusable package-neutral rules
├── repository/                 # Crystal Lattice policy
└── specifications/             # honest cross-package targets

maintainer/
├── README.md
├── specifications/
└── ...                         # standards-maintenance tooling
```

`docs/development/` is public guidance for contributors and agents doing
development. `maintainer/` is non-public material for developing and testing
the standards and agent workflows themselves.

## Artifact mapping

| Artifact | Crystal Lattice role |
|---|---|
| `<package>/README.md` | Concise purpose, installation, first use/build/test, and links |
| nearest `AGENTS.md` | Agent constraints, ownership, important files, verification, and routes |
| `<package>/docs/index.md` | Public package documentation map and preferred site landing page |
| `<package>/docs/quickstart.md` | Complete first-success package-user workflow |
| `<package>/docs/*.md` | Supported user guides, concepts, configuration, and troubleshooting |
| `<package>/docs/development/index.md` | Package maintainer map |
| `<package>/docs/development/*.md` | Current implementation, architecture, testing, and maintenance |
| `<package>/docs/development/specifications/` | Package-owned target specifications |
| `<package>/docs/reference/` | Optional generated or maintained reference |
| root `docs/development/` | Reusable standards, repository policy, architecture, and cross-package targets |
| `maintainer/` | Non-public standards and agent-workflow maintenance |

## Initial package profiles

| Scope | Target profile |
|---|---|
| `core/python` | Public SDK/application-layer package |
| `application/python` | Public application/CLI/service package |
| `packages/frontend-sdk` | Public SDK package |
| `packages/frontend-sdk-react` | Public integration package |
| `packages/frontend-rn-components` | Public shared component package |
| `packages/tool-host-node` | Public integration/tool-host package |
| `packages/react-native-mac-text-view` | Public native component package |
| Mobile and desktop applications | Public application packages |
| Bridge and cloud-orchestrator services | Public service packages |
| Individual `plugins/*` packages | README-first by default; add local guidance/docs when package needs exceed inherited rules |
| `plugins/docs/` | Shared plugin-authoring documentation domain |
| `docs_site/` | Documentation build and publication tooling |
| `maintainer/` | Non-public standards-maintenance domain |

This is a profile classification, not a requirement to generate every missing
file in one change. Core and application entry-point creation belongs to their
approved migration subtasks. Other packages adopt the profile on touch or
through separately scoped work.

## Ownership

Use the generic narrowest-authority rule.

- Package user and implementation documentation belongs with its package.
- Package-owned specifications belong under that package's development specs.
- Root cross-package specs are used only when independently owned packages must
  coordinate and no package is the honest normative owner.
- Root architecture pages are limited to genuinely cross-package structure.
- `docs_site/` owns site preparation, theme, navigation machinery, and build
  implementation.
- `maintainer/` owns the specification and validation of standards and agent
  workflow rules.

Do not put a page at root merely because several packages link to it. A package
that defines a shared abstraction may own its canonical contract.

## Shared plugin documentation

`plugins/docs/` is the shared consumer documentation domain for authors using
the plugin system. Start at `plugins/docs/index.md`.

It contains supported authoring guidance shared across provider, extension,
feature, application, and tool plugins.

Special rules:

- One plugin's internal behavior does not become a shared plugin contract by
  being used as an example.
- A substantial individual plugin may own specifications and development docs
  under its package.
- Framework protocol/specification ownership follows the package that defines
  the protocol, or root cross-package ownership when no package does.
- Shared plugin guides may summarize normative contracts for usability, but
  link the canonical specification and must not contradict it.
- Individual plugins inherit `plugins/AGENTS.md` unless package-specific rules
  justify a local AGENTS file.

## Documentation authority

Current package development pages may map target specifications to code. They
should say that they do not redefine the contract and identify:

- maintainer entry points;
- package responsibilities and non-responsibilities;
- implementation invariants;
- primary tests and manual/native boundaries.

Plugin authoring and package-user guides describe current supported behavior.
Unimplemented proposals remain in specifications and requirements.

## Source of truth and publication

Authored package and root pages are sources of truth.

`docs_site/scripts/prepare_mkdocs_site.py` assembles ignored
`docs_site/prepared/` input. MkDocs builds ignored `docs_site/dist/`.
Neither generated tree is edited directly.

The package registry introduced by the assembly subtask will declare public
package IDs, titles, roots, destinations, included sources, and development-doc
publication. Package `docs/index.md` is the preferred public landing page;
README is the fallback.

Excluded from public output by default:

- `AGENTS.md`;
- `maintainer/`;
- task files and plans;
- test and evaluation internals;
- generated source inputs that are not public pages.

Public development documentation remains publishable unless it contains
security-sensitive or internal operational information.

## Discoverability

Every package development index must be linked from its README, AGENTS, or
package docs index. A task-file link alone is insufficient.

Every public page must also be reachable through prepared-site navigation or a
linked package/root index after its package is registered.

Root `docs/development/index.md` routes to:

- reusable standards;
- repository policy;
- cross-package specifications.

Package indexes route to their user and implementation pages. Shared plugin
guides route from `plugins/docs/index.md`.

## Moving existing pages

The initial migration is deliberately bounded:

- move ownership-clear pages with minimal editorial changes;
- verify touched claims, links, examples, and contracts;
- preserve old public URLs through compatibility pages or redirects;
- avoid creating a second editable source;
- defer uncertain pages with likely owner, reason, and future trigger;
- do not reverse engineer large undocumented areas to fill the target tree.

The migration subtasks own Core, application/plugin, cross-package/reference,
navigation/compatibility, and final inventory work.

## Documentation build

From the repository root:

```bash
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

For local live reload:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs serve -a 127.0.0.1:8001)
```

Use `python docs_site/scripts/build_mkdocs_site.py` when the build should also
refresh committed generated reference snapshots. Do not run that convenience
script merely to inspect authored-page changes if snapshot updates are outside
the current task.