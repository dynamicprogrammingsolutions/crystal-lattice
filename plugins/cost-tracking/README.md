# cost-tracking

Generic, provider-agnostic cost tracking plugin for the Crystal Lattice
platform.

Cost-aware providers emit the `cost_tracking` capability tag and define a
cost bucket per request (the bucket base is config-alterable, the final
bucket is provider-defined). This plugin records per-request cost rows in a
SQLite store under the Crystal data directory, renders the store-backed
session total in the chat status bar (aggregated by workspace + session id),
and exposes session actions for a reset-aware cost report and a per-bucket
reset.

See `docs/development/overview.md` for the store schema, bucket rules, and
configuration.

## Development

```bash
python -m pip install -e "plugins/cost-tracking[dev]"
pytest plugins/cost-tracking/tests -q
```

The integration tests run a real `AgentApplication` request against a local
stub endpoint using the production provider and extensions
(`pytest plugins/cost-tracking/tests -m integration -q`).