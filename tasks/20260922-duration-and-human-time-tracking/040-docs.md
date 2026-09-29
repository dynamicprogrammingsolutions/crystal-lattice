Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/010-session-duration-store.md
- tasks/20260922-duration-and-human-time-tracking/020-tool-call-duration.md
- tasks/20260922-duration-and-human-time-tracking/025-tool-duration-store-totals.md
- tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md

# Documentation and Config Schema

Document the duration-tracking plugin, its store, metadata fields, status-bar elements, report, telemetry contract, and any new framework hook contract from subtask 020.

## Requirements checklist

- [ ] `plugins/duration-tracking/README.md` (and package docs where the cost-tracking layout has them) describes the store, config keys, metadata fields, status-bar elements and their config selection, report actions, and the telemetry ingestion contract (action shape, event types, batching, event ids, server-setting discovery).
- [ ] `plugins/timestamp-extension/README.md` reflects the migrated append-time stamping (per the 020 outcome) and cross-references the duration-tracking totals.
- [ ] Plugin docs describe any new framework hook contract from 020 (hook names, ordering, context facts, result shape, the "framework provides facts via context, plugins own measurement" rule) in the owning docs pages (e.g. `plugins/docs/feature-plugins.md`, `plugins/docs/provider-extensions.md`, `plugins/docs/actions.md` as applicable).
- [ ] All new config keys are discoverable through the config schema surfaces.
- [ ] Documentation is accurate against the implemented code, not aspirational.

## Supporting details

- Follow the cost-tracking package's documentation layout (`README.md` plus `docs/development/overview.md`).
- Documentation must be written after the 020 mechanism is settled; its hook-contract section depends on that outcome.
- Takes over `tasks/20260801-duration-and-stats-tracking/070-docs.md` (superseded; its `stats-storage.md` scope, `STATS_*` env vars, and session-stats-key documentation are dropped with the mechanisms they described).