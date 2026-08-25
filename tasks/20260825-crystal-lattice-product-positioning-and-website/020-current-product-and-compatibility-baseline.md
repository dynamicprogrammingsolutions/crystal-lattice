# Establish the Current Product and Compatibility Baseline

Create an evidence-backed catalog of current configured agents, providers,
accounts, application-wide features, defaults, optional behavior, limitations,
and verification state.

## Requirements checklist

- [ ] Configured-agent compatibility is cataloged separately from
      provider/account support and application-wide features.
- [ ] The catalog distinguishes repository presence, packaging, loading,
      default enablement, frontend support, automated verification, and
      real-provider verification.
- [ ] Important gaps and limitations are explicit without implying full parity
      with official upstream coding-agent products.
- [ ] The result is suitable as a maintained source for later website and
      contributor-facing compatibility content.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/010-website-documentation-and-content-specification-foundation.md`

## Scope

Audit:

- configured-agent profiles and model-family compatibility packages;
- provider routes and model discovery;
- API-key, subscription-account, and local-model authentication paths;
- system/developer instructions and tool surfaces;
- compaction, memory, skills, MCP, todo/planning, web, media, background, and
  provider-native behavior;
- session, action, notification, filtering, status, export, attachment,
  transparency, and configuration features;
- mobile, desktop, terminal, and HTTP rendering or execution support.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared program requirements, decisions, facts, handoff rules, output
   rules, and boundaries.
2. `landing_page/AGENTS.md:1-68` — package claim, research, privacy, and
   evidence boundaries.
3. `landing_page/docs/development/specifications/product-website-content/content-spec.md:14-218`
   — current product baseline, visitor groups, compatibility, transparency,
   features, customization, and connection distinctions that the catalog must
   eventually support.
4. `landing_page/docs/development/research/positioning-and-product-baseline.md:9-170`
   — current facts, hypotheses, compatibility recommendations, and open
   questions. Correct it rather than creating a competing baseline.
5. `landing_page/docs/development/research/evidence-index.md:18-75` — current
   product, plugin, compatibility, feature, and release source map.
6. `application/python/agent_terminal_app/default_config/config.json:460-568`
   and `application/python/agent_terminal_app/default_config/config.json:710-870`
   — active providers, globally loaded plugins, application settings, and
   configured-agent composition.
7. `plugins/docs/index.md:1-32` — plugin documentation router. Follow the
   owning package README, AGENTS, docs, source, and tests only for rows being
   classified or verified.

### Additional references

- `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
  — compatibility, current-state, transparency, contribution, and proof
  requirements.
- Mobile, desktop, terminal, frontend, and provider package documentation
  identified by the evidence index when a row requires client or real-provider
  verification.

## Known facts and supporting details

- The default configuration is coding-agent-oriented and combines model-family
  profiles, provider routes, global application plugins, and optional features.
- A compatibility package name is not evidence of complete parity with the
  official upstream product.
- Provider/account support and configured-agent behavior are separate axes.
- Application-wide session and transparency features may apply independently
  of a configured-agent profile.
- “Present in source,” “packaged,” “loaded,” “default-enabled,”
  “frontend-supported,” “automatically tested,” and “real-provider verified”
  are different states.
- Website content will consume the catalog but must not become authoritative
  for the underlying package behavior.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/current-product-and-compatibility-baseline.md`

Retained research package:

```text
landing_page/research/020-current-product-and-compatibility-baseline/
├── input-manifest.json
├── configured-agent-compatibility.csv
├── provider-account-compatibility.csv
├── application-feature-compatibility.csv
├── claim-evidence.jsonl
├── verification-summary.md
└── completion-manifest.json
```

Required updates:

- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  for corrected shared facts;
- `landing_page/docs/development/research/evidence-index.md` for authoritative
  catalog and verification routes;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`
  only for requirement evidence/status affected by delivered documentation,
  not for unimplemented public content.

## Scope boundaries

- Do not perform broad market, search-demand, community, or competitor
  research.
- Do not change `landing_page/src/content/`.
- Do not change the content target merely because a product capability exists.
- Do not create provider or compatibility claims without checking the owning
  source and appropriate verification boundary.
- Store disposable inspection output under
  `landing_page/artifacts/research/020-current-product-and-compatibility-baseline/`.

## Execution plan

Status: Draft

Define a structured catalog with explicit status dimensions and evidence
fields. Inventory default configured agents, providers, auth modes, global
plugins, and frontend support. Verify representative and decision-critical
claims against code/tests rather than inferring from package names.

Produce human-readable baseline findings and a machine-readable source suitable
for later website consumption without making the website authoritative for the
underlying product behavior.

### Implementation decisions and open questions

- Recommendation: use separate configured-agent, provider/account, and
  application-feature views.
- Recommendation: include a last-verified date and evidence route for
  drift-prone compatibility claims.
- Open question: choose the durable machine-readable catalog location after
  confirming which package or generator should own current product facts.

### Documentation

- Update website research baseline and evidence index.
- Add a focused compatibility finding page when substantive evidence exists.
- Do not publish target-only or unverified compatibility as current user
  documentation.

### Task checklist

- [ ] Define catalog schemas and status vocabulary.
- [ ] Inventory configured-agent profiles and compatibility packages.
- [ ] Inventory provider and account/auth modes.
- [ ] Inventory application-wide feature plugins and frontend support.
- [ ] Record default, optional, partial, experimental, planned, and missing
      behavior.
- [ ] Validate decision-critical claims.
- [ ] Produce maintainable human- and machine-readable outputs.
- [ ] Update content requirements and downstream handoffs.

### Requirement verification

- Catalog rows link current owning sources and evidence.
- No official-upstream parity claim is inferred from a compatibility package
  name.
- Default and optional behavior is distinguishable.
- Representative rows are checked against config, source, tests, and relevant
  frontend behavior.
