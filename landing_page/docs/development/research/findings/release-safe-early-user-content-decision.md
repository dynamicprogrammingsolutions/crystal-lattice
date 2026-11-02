# Release-Safe Early-User Content Decision

Status: focused source refresh accepted; canonical public tables pending.

Updated: 2026-10-24

## Approved homepage relationship

The first-user homepage introduces Crystal Lattice as an application for
configurable AI coding agents. It uses **configured agent** for the named
configuration selected by a session and **harness** for materially variable
tool implementations, provider integration, context behavior, and controls.

The accepted concise direction is:

> Crystal Lattice includes configured agents with Codex-oriented,
> Claude-compatible, Gemini-oriented, and other harnesses. These are Crystal
> Lattice implementations, not the official upstream applications.

Each family uses the qualifier supported by its package evidence. The homepage
does not render the exhaustive catalogue; it provides recognizable examples
and routes detailed questions to the compatibility page.

## Approved compatibility content model

The first public catalogue uses one `/compatibility` route with three concise
canonical tables:

1. **Harnesses** — selected differentiating capabilities, with related tool
   implementations combined into meaningful rows.
2. **Providers** — Basic API support, subscription authentication, native
   extras, and concise conditions/limitations.
3. **Plugins and application features** — selected product behavior groups,
   not the complete package inventory.

Configured agents, harnesses, providers, and plugins remain separate axes. The
catalogue must not imply that a provider is a harness, a harness is a named
agent, or every plugin applies to every agent.

Configured-agent examples are introduced by the homepage and harness context.
Exact agent/provider/model/package evidence remains available in progressive
detail and the internal projection rather than becoming a fourth exhaustive
primary table.

The plugin table uses user-meaningful groups such as session organization,
history/actions, provider controls, usage/cost, attachments/assets, context,
MCP, export/sharing, and cloud workspaces.

## Status model

The proposed public status vocabulary distinguishes:

- Included;
- Available;
- Conditional;
- Experimental;
- In development;
- Planned;
- Unsupported;
- Not applicable;
- Not verified;
- Developer/internal.

Availability, maturity, and verification remain separate underlying
properties. The website must not derive one green checkmark from source
presence alone.

## Version-two projection

The review package is maintained under:

`landing_page/research/release-safe-early-user-website/`

It contains:

- a deterministic four-view projection;
- a human-readable rendering;
- an input/hash manifest;
- focused source-drift records;
- explicit post-baseline refreshes.

The projection currently contains:

- 20 configured agents in eight relationship groups;
- six harness families with detailed capability rows;
- ten provider/account routes;
- 69 plugin projects separated into included, optional,
  distribution-specific, and developer/internal groups.

## Focused source refresh

The accepted baseline remains the source for unchanged rows. Focused
verification identified these material post-baseline changes:

- Anthropic native compaction is now conditional current behavior rather than
  planned, and native context editing is implemented as a separate
  capability-gated extension.
- Codex `exec_command` and `write_stdin` are current default unified-exec
  tools; retained array/string shell modes are optional alternatives.
- Claude-compatible compaction now includes a background application plugin
  with notifications, cancellation, retry, and pre-commit snapshots.
- `embedded-workspace-settings`, `interleaved-thinking`, and
  `shell-tool-settings` were added to the plugin inventory.
- all 20 configured agents now have current display titles, descriptions, and
  ordering; their accepted provider/model/plugin identity did not drift in the
  focused comparison.

Focused local suites passed 185 tests across those changed areas. No hosted
provider request was run, so hosted availability and account/model acceptance
remain unverified.

## Current checkpoint

The focused source refreshes are accepted. The complete version-two projection
is retained as internal evidence and is not intended to render directly.

No compatibility route, component, navigation, or homepage link has been
implemented. Canonical row selection and UI work are paused behind
`tasks/20261024-production-staging-website-channels.md`.