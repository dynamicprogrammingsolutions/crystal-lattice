# Product Website Research Method

This method supports Crystal Lattice product positioning and website content.
It does not require every source or workstream for every content decision.

## Principles

- Start with revisable hypotheses.
- Select sources according to the decision being made.
- Preserve source provenance and observation dates.
- Keep source facts separate from inferred classifications.
- Preserve supporting, contradictory, ambiguous, and irrelevant evidence.
- Use a bounded pilot before broad collection.
- Expand productive branches and stop noisy ones.
- Require human review for decision-bearing classifications.
- Do not treat one evidence type as answering a different question.
- Promote research into public content only through an explicit content
  decision.

## Evidence Types

### Product and Repository Evidence

Answers:

- what is implemented;
- what is default-enabled;
- what is optional;
- which clients and providers support it;
- what tests and release evidence exist.

It does not establish market value.

### Search Demand and Result Composition

Answers:

- what language people search;
- relative demand and competition;
- whether queries lead to products, documentation, communities, jobs, or
  unrelated meanings.

It does not establish product fit, conversion, or willingness to pay.

### Community and Question Evidence

Answers:

- how users describe problems;
- current workarounds;
- desired outcomes;
- objections and contradictions.

Discussion counts are bounded source/query yields, not market size.

### Competitor and Substitute Evidence

Answers:

- established category language;
- product packaging;
- feature and compatibility claims;
- pricing and calls to action;
- common proof and trust patterns.

Public claims do not establish actual quality, revenue, adoption, or customer
satisfaction.

### Product Issues and Feature Requests

Answers:

- recurring failure shapes;
- missing workflow details;
- implementation and maintenance pressure.

Issue frequency does not establish buyer demand or willingness to switch.

### Early-User Observation and Interviews

Answers:

- comprehension;
- first-use friction;
- perceived value;
- switching reasons;
- trust and control expectations;
- reactions to capabilities users did not request beforehand.

Interview evidence is qualitative and must preserve participant privacy and
selection bias.

### Experiments and Observed Behavior

Answers:

- relative comprehension and action;
- whether a proposition or path performs better under the tested conditions;
- whether visitors express interest in a future service.

An experiment result remains bounded by its traffic, audience, duration, and
measurement quality.

## Shared Retained Record Shape

Use a small common base with source-specific extensions:

- stable record ID;
- source type and source ID;
- source URL;
- publication date and precision;
- observation date;
- query, route, or experiment ID;
- bounded excerpt or source-fact fields;
- user problem or job;
- product stage or context;
- workaround;
- requested outcome;
- explicit commercial or switching signal;
- supporting, contradictory, ambiguous, or irrelevant direction;
- source facts;
- inferred fields and confidence;
- review state and reviewer note;
- collection/version metadata.

## Built-In Feature Opportunity Review

For each plugin or user-facing feature, record:

- current user-visible behavior;
- default versus optional state;
- configured agents, providers, and clients affected;
- material limitations;
- user job or pain hypothesis;
- likely search and discussion language;
- competitor support;
- known workaround or separate product;
- explicit versus latent value;
- trust, security, or complexity risk;
- best proof or demonstration;
- recommended research branch.

Create additional handoffs only after this review identifies a coherent,
decision-useful cluster.

## Pilot and Expansion

Before broad collection:

1. define the decision;
2. record hypotheses and contradictory possibilities;
3. assess source access, permitted use, cost, and bias;
4. run a bounded pilot;
5. manually review representative records;
6. measure relevance, duplication, and new terminology;
7. recommend expand, refine, retain as control, defer, or stop;
8. obtain approval before paid or materially expanded collection.

Do not expand only to reach a target count.

## Manual Review

Review samples across:

- source;
- query or problem family;
- predicted relevance and direction;
- high and low engagement;
- current and older evidence where timing matters;
- direct support and counterevidence.

If a conclusion-bearing stratum shows material error, correct the method,
expand review, or withdraw the conclusion.

## Confidence

Use labels such as:

- **Robust:** supported by several appropriate evidence sources with passed
  review and no unresolved material contradiction.
- **Moderate:** useful supporting evidence with meaningful limitations.
- **Exploratory:** plausible direction needing focused validation.
- **Contradictory:** important evidence supports materially different
  interpretations.
- **Unresolved:** evidence is absent, too weak, or too unreliable for a
  decision.

Confidence applies to a conclusion, not to an entire source or task.

## Privacy and Copyright

- Do not retain credentials, browser sessions, private content, or unnecessary
  personal data.
- Keep interview recordings and full transcripts private unless explicit
  consent and a defined retention need justify otherwise.
- Commit anonymized findings and minimized evidence.
- Retain bounded excerpts rather than complete pages or discussion threads.
- Record access and permitted-use boundaries for active sources.
- Keep raw API responses, downloaded pages, browser captures, and caches under
  ignored `landing_page/artifacts/`.

## Content Promotion

The path from finding to public copy is:

```text
evidence
  -> reviewed finding
  -> content recommendation
  -> approved content decision
  -> specification update when the target changes
  -> current public content
  -> build and verification
```

Research pages may preserve several competing directions. Public content uses
only the direction approved for that website release.

## Progressive Revision

Research should not block a useful early-user site.

- The release-safe baseline uses current product truth.
- The first research-informed update waits for built-in feature, search,
  community, and competitor evidence.
- The next update uses early-user and remote-access findings.
- A larger validated release follows synthesis and proposition experiments.
- Production measurement informs bounded later changes.
