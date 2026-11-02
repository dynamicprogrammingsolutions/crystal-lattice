# Release-Safe Early-User Website Projection

Status: focused source refresh accepted; complete projection retained as
internal evidence; canonical public selection pending.

This retained package derives the proposed public compatibility catalogue from
the accepted product baseline without rewriting that completed evidence
package.

## Outputs

- `compatibility-projection-v2.json` — machine-readable four-view projection:
  configured agents, harness capabilities, provider support, and
  plugins/application features.
- `compatibility-projection-v2.md` — human review rendering.
- `drift-report.json` and `drift-report.md` — focused comparison between the
  accepted source revision and the current product source.
- `input-manifest.json` — source revisions, input hashes, generator, outputs,
  and review state.

## Maintained inputs

- `projection-config.json` — approved grouping, labels, status vocabulary,
  focused verification records, and post-baseline plugin supplements.
- `generate_compatibility_projection.py` — validation and deterministic
  projection generator.

## Regeneration

From the repository root:

```bash
python \
  landing_page/research/release-safe-early-user-website/generate_compatibility_projection.py

python \
  landing_page/research/release-safe-early-user-website/generate_compatibility_projection.py \
  --check
```

The generator fails when configured-agent IDs drift, current plugin additions
are not classified, accepted plugin projects disappear, internal task paths
leak into the proposed public projection, or generated files differ.

## Boundaries

- The accepted compatibility baseline remains authoritative for unchanged
  rows.
- Focused current-source refreshes are explicit in `drift-report.*`.
- No hosted provider request was run for this projection.
- The complete output is not the public website design. A later canonical
  selection will derive three concise tables for harnesses, providers, and
  plugins/application features.
- Route/component implementation and responsive/accessibility verification
  remain later task stages.