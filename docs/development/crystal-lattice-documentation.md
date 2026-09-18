# Crystal Lattice documentation conventions

Use the [documentation and specification guide](documentation.md) for file
roles, writing guidance, requirements, testing strategy, and generated
documentation. This page adds only Crystal Lattice paths and repository
decisions.

## Repository map

Package documentation normally uses whichever parts of this structure improve
the package:

```text
<package>/
├── README.md
├── AGENTS.md
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── <user-topic>.md
    ├── development/
    │   ├── index.md
    │   ├── <developer-topic>.md
    │   └── specifications/
    │       └── <capability>/
    └── reference/
```

Every entry is conditional. Small plugins and internal packages may remain
README-only or inherit their nearest `AGENTS.md`. A standalone page is valid
when a directory and index would add no useful navigation.

Repository-wide locations are:

```text
docs/development/
├── documentation.md
├── crystal-lattice-documentation.md
└── specifications/<capability>/

plugins/docs/                         shared plugin-authoring guidance
maintainer/docs/                      cross-cutting maintainer concepts and results
maintainer/docs/development/specifications/
                                      cross-cutting guidance targets
maintainer/<tool>/docs/development/specifications/
                                      package-owned maintainer-tool targets
docs_site/packages.toml               public package-documentation registry
docs_site/prepared/                   generated site input
docs_site/dist/                       generated site output
```

## Place documentation with the behavior

Package user and developer documentation normally stays with the package.
This includes `core/python`, `application/python`, frontend packages, mobile
and desktop applications, services, and substantial plugins.

A package may define a specification when it defines behavior, even when it
also implements broader behavior. For example, a frontend may define
package-specific UX requirements on top of behavior shared across frontends.
Link the broader specification and do not silently weaken it.

Use root `docs/development/specifications/<capability>/` only when independently
maintained packages must coordinate and no package defines the complete
behavior. Name the specification after the capability. Cross-package use or
portability may be described in its scope but is not a required title or
directory prefix.

Keep root `docs/` for repository entry points, project-wide development
guidance, cross-package architecture, and cross-package specifications. Do not
move package documentation to root merely because several packages link to it.

## Plugin documentation

`plugins/docs/` is the shared user-documentation area for authors using the
plugin system. Start at `plugins/docs/index.md`.

Use it for supported behavior shared by provider, extension, feature,
application, and tool plugin authors. Keep one plugin's configuration,
limitations, implementation, and specification with that plugin unless the
behavior is genuinely part of the common plugin interface.

An individual plugin normally inherits `plugins/AGENTS.md`. Add a local
`AGENTS.md` or more package documentation only when the plugin has useful
instructions or subjects not covered by the inherited guidance and README.

## Specifications, requirements, and tasks

Package specifications normally live at:

```text
<package>/docs/development/specifications/<capability>/
```

Cross-package specifications live at:

```text
docs/development/specifications/<capability>/
```

Cross-cutting guidance and workflow specifications live at:

```text
maintainer/docs/development/specifications/<capability>/
```

Specifications for a maintainer tool live with that tool, for example under
`maintainer/agent-evaluation/docs/development/specifications/` or
`maintainer/guidance/docs/development/specifications/`.

The complete multi-file shape is optional. Use one specification page,
requirements, a testing strategy, separate product and technical pages, or
decision records only when each improves understanding.

Crystal Lattice requirements use stable capability IDs when durable tracking
is useful. Keep these states separate:

- implementation: `Not started`, `In progress`, `Implemented`, `Deferred`, or
  `Removed`;
- verification: `Unverified`, `Automated`, `Human verified`, or
  `Not applicable`;
- documentation: `Pending`, `Documented`, or `Not applicable`.

Use `Primary evidence` for the smallest direct validation reference. Put shared
task, pull-request, and commit references once below the table instead of
repeating them in every row.

Tasks under `tasks/` own approval, execution plans, dependencies, findings, and
completion. A task links relevant requirement IDs without becoming a second
specification.

`maintainer/guidance/current/sections/tasks-v7.md` is the maintained
task-guidance source. Compilation writes the repository/runtime canonical
`agents/TASKS-v7.md`. Check or explicitly write current compiled guidance
with:

```bash
python -m maintainer.guidance check \
  --bundle maintainer/guidance/current \
  --target maintainer/guidance/targets/crystal-lattice \
  --destination .
python -m maintainer.guidance write \
  --bundle maintainer/guidance/current \
  --target maintainer/guidance/targets/crystal-lattice \
  --destination .
```

The application ships a synchronized copy at
`application/python/agent_terminal_app/default_config/TASKS_v7.md`. Update or
check it with:

```bash
python scripts/sync_tasks_v7.py
python scripts/sync_tasks_v7.py --check
```

Published user and developer documentation describes available behavior.
Target-only user text may be drafted on a development branch with a visible
`Not implemented` marker, but it is not published as current guidance by
default. Specifications may contain a short implementation note when it helps
readers understand a meaningful target/implementation difference; requirements
remain the detailed status record.

## Agent routing and maintainer material

Before creating, moving, or materially restructuring documentation or
specifications, read:

- the nearest package README and `AGENTS.md`;
- [Documentation and specification guide](documentation.md);
- this page.

A local factual correction does not require unrelated structure guidance when
the page, reader, and maintained source are already clear.

When changing these conventions, task guidance, publication rules, or their
behavioral evaluation, additionally read:

- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`;
- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/requirements.md`;
- the active task.

`maintainer/docs/` contains cross-cutting concepts, workflows, current status,
and interpreted evaluation results. Reusable maintainer tools keep their
documentation and specifications with the package. Suite scenarios and frozen
records stay with their owning suite. This domain is not required reading for
package users and is excluded from public documentation by default.
Production and package tests remain with their owning packages.

## Publication and generated documentation

Authored package and root pages are maintained sources.
`docs_site/packages.toml` declares public package identity, source,
destination, included inputs, and development-documentation publication.

The preparation step assembles ignored `docs_site/prepared/` input. MkDocs
builds ignored `docs_site/dist/`. Do not edit either generated tree directly.

Excluded from public output by default:

- `AGENTS.md`;
- `maintainer/`;
- task files and plans;
- evaluation internals;
- generated source inputs that are not themselves public pages.

From the repository root:

```bash
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Use `python docs_site/scripts/build_mkdocs_site.py` only when the work also
intends to refresh committed generated reference snapshots.

If a prepared page is wrong, fix its authored source or generator and run the
normal preparation step when it is in scope. If preparation fails, leave the
prepared and built trees unchanged, report the failing command or dependency,
and state the remaining action.

## Moving existing pages

Move a maintained page instead of keeping two editable copies. Update its
owning README or index, inbound links, package registry entry, and navigation
inputs as applicable.

Preserve an existing public address through the compatibility behavior owned
by the documentation-site navigation work unless a breaking change is
explicitly approved. Compatibility pages and redirects are not maintained
copies of the moved content.

Verify claims, commands, examples, and links touched by the move. If a page
would require broad investigation to make reliable, leave it in place or
record a focused follow-up with a likely package and useful trigger. Do not
reconstruct large undocumented areas merely to make the repository match the
illustrated structure.