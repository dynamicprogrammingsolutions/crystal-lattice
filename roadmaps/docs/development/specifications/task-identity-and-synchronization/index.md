# Roadmap task identity and synchronization

This specification defines roadmap task identity,
external and internal IDs, dependency normalization, Markdown links, CSV
normalization, and Google Sheets convergence.

Owner: `roadmaps/`

## Specification files

- [Technical specification](technical-spec.md): schema, classification, ID
  generation, alias resolution, normalization, synchronization, migration,
  failure behavior, and security.
- [Requirements](requirements.md): stable target requirements and live
  implementation evidence.

## Scope

The target:

- makes `task` the unique authored row identity;
- accepts a task Markdown path, task-directory path, or free task name;
- supports optional, nonunique external IDs;
- generates unique short internal IDs;
- stores dependencies canonically as internal IDs;
- accepts useful aliases during editing and rewrites them canonically;
- updates references when regenerated IDs change;
- converges CSV, generated Markdown, and Google Sheets on one normalized table.

## Current contract

The implemented CSV and synchronized Google Sheet use:

```csv
task,external_id,internal_id,title,purpose,priority,status,declared_dependencies,inferred_dependencies,notes
```

The previous `key`/`main_id` schema was migrated together across the local CSV,
generated Markdown, and Google Sheet. The package README describes the current
commands and editing workflow.

## Goals

- Let people identify tasks naturally without maintaining a separate stable
  key.
- Keep externally assigned IDs visible without requiring them to be unique.
- Make dependency references short, unique, deterministic, and mechanically
  maintainable.
- Allow spreadsheet edits without leaving stale IDs or mixed dependency forms.
- Preserve strict dependency ordering and dry-run-first synchronization.

## Non-goals

- Inferring arbitrary dependencies from task prose.
- Treating one shared external ID as an implicit dependency on every matching
  task.
- Automatically sorting roadmap rows.
- Creating task files for free-name placeholders.
- Turning spreadsheet synchronization into an automatic merge system.
- Storing Google credentials or credential paths in the repository roadmap
  config.

## Primary acceptance examples

### Task Markdown

```text
task:
tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md

external_id:
CL-368

internal_id:
CL-368-040
```

The generated task title links directly to the Markdown file.

### Task directory

```text
task:
tasks/20260804-open-source-public-release

internal_id:
0804-OS
```

The generated task title links to `000-main.md` inside the directory.

### Free task name

```text
task:
website-ios-review

internal_id:
WEB-IOS
```

The generated task title has no repository link.

### Regenerated reference

If a row changes from generated ID `0804-OS-040` to external-ID-based
`CL-368-040`, dependencies containing the old ID resolve through the row's
previous internal ID and are rewritten as `CL-368-040`.

### Ambiguous external ID

If `CL-368` belongs to both `CL-368-010` and `CL-368-020`, a dependency entered
as `CL-368` is rejected with both matching internal IDs. It is never expanded
silently.