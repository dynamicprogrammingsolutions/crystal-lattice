# Establish Production Measurement and Iteration

Adopt a privacy-compatible method for observing website comprehension and
actions, establish a bounded post-release learning loop, and keep public
privacy statements aligned with actual measurement.

## Requirements checklist

- [ ] Measurement has an approved purpose, event taxonomy, data-minimization
      model, retention boundary, access policy, and privacy disclosure.
- [ ] The system can distinguish key website actions such as installation,
      downloads, docs, compatibility, customization, contribution, and
      remote-access interest where approved.
- [ ] Website signals are interpreted with source, traffic, audience, and
      attribution limitations.
- [ ] Early post-release findings produce bounded content or experiment
      recommendations rather than uncontrolled continuous redesign.
- [ ] Privacy, support, operational, and product documentation remains accurate
      after implementation.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`

## Candidate approaches

- aggregate CDN/server logs;
- privacy-preserving first-party analytics;
- explicit waitlist or feedback forms;
- release/download events;
- documentation and compatibility route use;
- consented product activation correlation where separately authorized.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared measurement question, evidence distinctions, output rules, privacy,
   current-content, and remote-mutation boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md:1-119`
   plus its production delivery evidence and current deployed routes. Stop if
   incomplete.
3. `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
   — especially `WEB-MEASURE-001` and public content requirements whose
   interpretation measurement may inform.
4. `landing_page/docs/development/research/research-method.md:93-102`,
   `landing_page/docs/development/research/research-method.md:175-217`, and
   `landing_page/docs/development/research/research-method.md:219-228` —
   experiment evidence, confidence, privacy, content promotion, and bounded
   iteration.
5. `landing_page/src/content/markdown/privacy.md:71-104` — current website
   logs, analytics, support correspondence, and privacy statements.
6. Current deployment/CDN, download, support, store, and product telemetry
   documentation for every candidate event source.

## Known facts and supporting details

- The current public privacy policy says the website does not use third-party
  advertising trackers or website analytics.
- Measurement must begin with decisions and a minimal event taxonomy, not tool
  selection.
- Page views, clicks, downloads, first connection, first request, return use,
  waitlist signup, and payment are different signals with different privacy
  and attribution boundaries.
- Website traffic may be small and non-representative during early release.
- Material new product or positioning scope belongs in a new approved task;
  this task owns bounded iteration.

## Expected outputs

Current implementation documentation:

- `landing_page/docs/development/measurement.md`

Retained measurement package:

```text
landing_page/research/180-production-measurement-and-iteration/
├── measurement-decision.md
├── event-taxonomy.csv
├── privacy-and-data-map.md
├── implementation-validation.md
├── initial-production-findings.md
└── completion-manifest.json
```

Implementation outputs:

- approved analytics/log/event code and configuration in the owning package or
  deployment source;
- focused tests for event shape, minimization, and failure behavior;
- updated `landing_page/src/content/markdown/privacy.md` and related public
  content committed with the behavior change;
- bounded content recommendations and any separately approved follow-up task
  proposals.

Disposable output:

- `landing_page/artifacts/research/180-production-measurement-and-iteration/`
  for raw reports, exports, debug events, and temporary analyses.

## Scope boundaries

- Do not enable tracking, create accounts, send production events, or change
  privacy behavior before approval.
- Do not collect message content, prompts, credentials, private sessions, or
  unnecessary persistent identifiers.
- Do not treat low-volume early traffic as representative market evidence.
- Do not continuously redesign the website without an explicit bounded
  decision and content update.
- Do not update public privacy claims before the implementation they describe
  is committed and ready for release.

## Execution plan

Status: Draft

Define the decisions measurement should support before selecting tooling.
Compare privacy, data ownership, retention, operational burden, cost, and
signal quality. Update privacy content and obtain any required legal/product
approval before enabling collection.

Validate events without recording unnecessary content or identity. Establish a
review cadence, interpretation boundaries, and a small improvement backlog.
Use later tasks for material new product or positioning scope.

### Implementation decisions and open questions

- Decision: the current no-third-party-analytics privacy statement remains
  authoritative until changed with approved implementation.
- Recommendation: collect the minimum aggregate events needed for explicit
  decisions.
- Open questions: selected tool, consent model, retention period, cross-product
  attribution, and whether server-log analysis is sufficient.

### Documentation

- Document the delivered measurement implementation and operations.
- Update public privacy content with the code/configuration that changes
  behavior.
- Preserve detailed experiments and analyses under package research ownership.

### Task checklist

- [ ] Define measurement decisions and event taxonomy.
- [ ] Compare candidate approaches.
- [ ] Approve privacy, retention, and access model.
- [ ] Implement and test selected measurement.
- [ ] Update privacy and current development documentation.
- [ ] Validate production events and data minimization.
- [ ] Establish review cadence and bounded iteration rules.
- [ ] Produce initial post-release findings and recommendations.

### Requirement verification

- Captured data matches documented events and excludes unapproved content or
  identifiers.
- Privacy statements match actual production behavior.
- Events can be traced through the intended reporting path.
- Recommendations state traffic, attribution, and confidence limitations.
