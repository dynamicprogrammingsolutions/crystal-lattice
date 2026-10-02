# Current Product and Compatibility Baseline — Verification Summary

Status: Accepted and complete
Observation cutoff: October 1, 2026
Product source revision:
`add5f5e71de3bb1676851bb840dfd77620f63ddb`

## Retained review package

- Three authoritative matrix concepts:
  - 66-project plugin feature catalog;
  - 10 providers × 19 native/provider features = 190 cells;
  - 12 model-family groups × 21 features = 252 cells.
- JSON and long-form CSV for each authoritative matrix.
- One generated human-readable review:
  `compatibility-matrices.md`.
- Supporting normalized evidence:
  - 20 configured-agent rows;
  - 7 provider/account rows;
  - 33 application-feature rows, comprising 28 globally selected plugin
    specifications and 5 explicitly scoped optional features.
- 24 stable claim-evidence records
- all 60 normalized catalog rows, 24 claim records, and exhaustive matrices
  are `accepted`;
- the compact website projection is accepted as a downstream draft that the
  website rewrite may refine.

The authoritative matrices are product-named and contain no numeric task
identifier. They distinguish plugin lifecycle, provider-native capabilities,
model-family tool behavior, native and non-native web search, profile and
provider compaction, explicit planned cells, prerequisites, limitations, and
review state.

The supporting catalogs distinguish source presence, packaging selection,
loading scope, default or optional enablement, HTTP, terminal, mobile, desktop,
automated verification, real-provider verification, limitations, confidence,
and review state.

Validation:

```text
.venv/bin/python \
  landing_page/research/020-current-product-and-compatibility-baseline/extract_baseline.py \
  --check

.venv/bin/python \
  landing_page/research/020-current-product-and-compatibility-baseline/generate_compatibility_matrices.py \
  --check

.venv/bin/python \
  landing_page/research/020-current-product-and-compatibility-baseline/generate_website_compatibility_data.py \
  --check
```

Current results:

- `catalog extraction check passed`
- `compatibility matrix check passed`
- `website compatibility data check passed`

## Delegated evidence collection

The broader audit used nine fresh sessions after calibration:

| Batch | Model / effort | Result | Estimated USD |
|---|---|---:|---:|
| Claude / Anthropic | GPT-5.6 Terra / high | complete | 1.2504302 |
| Qwen / Gemini / Grok / Kimi / GLM | GPT-5.6 Terra / high | complete | 1.0451172 |
| Ollama / Fireworks / Z.ai | GPT-5.6 Terra / high | complete | 0.6947382 |
| specialist agents and distribution | GPT-5.6 Terra / high | complete | 1.3537684 |
| session-list organization | GPT-5.6 Luna / high | complete | 0.17986374 |
| history / compaction / export / background | GPT-5.6 Luna / high | complete | 0.18058832 |
| configuration and transparency | GPT-5.6 Terra / high | complete | 1.2181784 |
| production client matrix | GPT-5.6 Luna / high | complete | 0.25929422 |
| contradiction challenge | GPT-5.6 Terra / xhigh | complete | 2.306117 |

Broader-audit API-equivalent estimate: **$8.48809568**.

The prior model calibration cost **$14.49803498**, so total audit-agent
evidence generation is **$22.98613066**. These are ChatGPT-route
API-equivalent estimates, not subscription invoices.

Every broader-audit run wrote a claim map before the checkpoint and produced a
complete packet. One wave-1 packet finished before the checkpoint monitor
serialized its state; its stored `pending` label is bookkeeping-only and the
claim map existed after approximately two minutes.

Disposable worker packets remain under the ignored task artifact directory.
Only independently reviewed classifications and minimized claims are retained
here.

## Independently reproduced verification

### Configured agents and providers

- Codex shell/model selection: 46 tests passed.
- Codex prompt selection: 30 tests passed.
- Reference OpenAI-compatible provider: 121 tests passed.
- Anthropic provider/transport/cache/reasoning/tool/usage: 58 tests passed.
- OpenRouter provider/capability/tool/reasoning/usage/web/attachment:
  94 broader tests and 80 focused tests passed.
- Claude tools: 84 tests passed, 1 integration case deselected.
- Image provider/attachment: 9 tests passed.

### Session, history, and application behavior

- Public session-list HTTP contract: 5 tests passed; 6 integration-marked
  cases deselected.
- Core session listing/filter/application-plugin behavior: 33 tests passed.
- Snapshot, asset, projection, JSON projection, and notification behavior:
  61 tests passed.
- Cloud-agent focused behavior: 12 tests passed; 36 deselected.
- Cloud bundle/source staging: 12 tests passed.

### Frontend and public adapter boundaries

- Focused frontend SDK tests: 88 passed.
- Frontend SDK React bindings: 6 passed in the independently selected slice.
- Real local FastAPI + FetchTransport + production RestAgentBackend:
  - first rerun: 19 passed, 2 failed because fresh plugin installation did not
    make the backend ready before the harness startup timeout;
  - immediate warm-cache rerun: 21 passed.
- Session-status integration: 1 passed.
- Action-display integration: 1 passed.

The backend/SDK boundary is therefore passing but startup-sensitive when path
plugins must be installed into a fresh temporary cache.

## Main catalog conclusions proposed for review

### Configured agents

- Profiles are Crystal Lattice compatibility configurations, not official
  upstream products, accounts, or sessions.
- Provider route and account/auth mode remain separate from model-family
  prompt/tool behavior.
- Codex, Claude, Qwen, Gemini, Grok, Kimi, GLM, Ollama, Fireworks, Z.ai,
  specialist cloud-author, and image-generation profiles have distinct
  prerequisites and limitations.
- Ollama model IDs ending in `:cloud` still use the configured localhost
  OpenAI-compatible route; the suffix alone does not prove a hosted account,
  remote execution, or local weight placement.

### Provider/account routes

- OpenAI API key, saved ChatGPT, OpenRouter, direct Anthropic, local Ollama,
  Fireworks, Z.ai, and OpenRouter image generation are materially different
  routes.
- Model discovery, tool/reasoning capability, cost semantics, and attachment
  support are route- and model-dependent.
- No current hosted-provider success, account entitlement, or invoice
  reconciliation was established by this audit.

### Application features and clients

- Session organization, actions, titles, bounded search, pin/archive/status,
  timestamps, ordering, summaries, assets, snapshots, settings, plugins,
  request controls, system-message inspection, MCP control, cost, and message
  timing have substantial current source/API support.
- Message export, Gemini compaction, duration tracking, and sleep prevention
  are source-present but optional-not-default.
- FastAPI and the production SDK are the strongest common execution boundary.
- Mobile and desktop contain production generic consumers, but native UI
  suites were not run.
- The interactive terminal has sessions, history mutation, settings, plugin
  toggles, cancellation, reasoning/tool rendering, and raw UI schema, but no
  generic application/session/message action executor.
- Standalone CLI/Python provides synchronous persisted runs and projected
  history; it is not an interactive terminal or a general action API.

## Material contradictions and gaps

### Prompt/tool contract

Five checked-in Codex-family profiles select the generic GPT-5 prompt, which
states that `update_plan` is available. The selected Codex descriptor and a
direct configured-class probe do not register it. Checked-in subagent and
request-input schemas under the Codex reference directory are reference
material rather than selected default tools.

`codex-openai-api` selects a distinct GPT-5.4 prompt and is not part of this
specific mismatch.

### Package provenance

The selected Claude prompt presents official-Claude-CLI language, while the
package provenance identifies the implementation as an independent,
unaffiliated Crystal Lattice compatibility package. Public/catalog language
must follow the package provenance boundary.

### Source/test drift

- Grok source and descriptor include `bash`; two tests expect it absent.
- Aggregated application status schema stamps an `order` field; one plugin
  test expects raw schema without it.
- The current event-store list contract returns an envelope mapping. The
  challenge did not find a current focused test that incorrectly expects a
  direct iterable list, although an earlier combined plugin run reported
  envelope-related failures.
- Deleting a persisted session after its historical agent is removed from
  configuration reproducibly raises before deletion.

### Effective loading

The checked-in config and packaging closure are established, but full clean
default plugin instantiation remains unresolved. Fresh offline probes stopped
before class import because local build prerequisites such as setuptools/wheel
were unavailable through the intentionally disabled package index.

The earlier generated-cache `pydantic_core` import symptom was neither
reproduced as a fresh clean-start defect nor proven to be stale-cache
contamination. A fresh supported source-install or bundled-runtime smoke is
still required.

### Incomplete verification

- No hosted OpenAI, ChatGPT, OpenRouter, Anthropic, Fireworks, Z.ai, image, or
  Ollama-model request was authorized or run.
- No optimized executable/archive, bundled-Python artifact, cloud image, or
  deployed cloud runtime was built and executed.
- Native mobile and macOS UI suites were not run.
- ChatGPT-auth selected tests timed out.
- Message-export tests remained timeout-incomplete after declared Python
  dependencies were installed; browser, pandoc/LaTeX, SMTP/Keychain, and
  native-share paths remain unrun.
- Default-config Claude prompt tests remain blocked by a generated plugin-cache
  compiled dependency problem in this local environment.

## Human review decisions approved

Approved by the user on October 1, 2026:

1. Accept the compatibility-profile wording and the explicit exclusion of
   official upstream account/session parity.
2. Accept `partial` as the default capability classification for configured
   provider-backed profiles without dated real-provider evidence.
3. Accept the Codex `update_plan` prompt/tool mismatch as a current limitation
   and contributor-facing gap.
4. Accept generic terminal action execution as unsupported while retaining
   partial terminal support for native session/settings/plugin workflows.
5. Accept `:cloud` Ollama models as “cloud-named identifiers through the
   configured local Ollama route,” with account/execution semantics unknown.
6. Accept source/test drift and historical-agent deletion as explicit current
   limitations rather than normalizing failing tests into passes.
7. Accept selected source/packaging-builder evidence while leaving clean
   default loading and produced-artifact execution unresolved.
8. Accept generic mobile/desktop production-consumer support with native UI
   verification still unknown.
9. Accept provider-reported and locally estimated cost values as transparency
   data, not billing/invoice truth.

All 20 configured-agent rows, 7 provider/account rows, 33 application-feature
rows, and 24 claim records now carry `accepted`.

## Canonical website projection accepted as draft

Accepted by the user on October 2, 2026 as a draft input for downstream
website work. The projection contains:

- 9 application/session feature rows selected to avoid provider/tool overlap;
- 9 provider rows with 6 user-relevant native-capability columns;
- 71 package-specific current or planned tool rows across 6 model-family
  bundles.

Files:

- `website-compatibility-selection.json` — internal selection, task/source
  references, and display overrides;
- `generate_website_compatibility_data.py` — canonical validation and public
  transformation;
- `website-compatibility-data.json` — machine-readable public projection;
- `website-compatibility-data.md` — human review rendering.

The generator validates current tools against package descriptors, planned
tools against maintained task files, simple provider cells against the
exhaustive provider matrix, and feature rows against catalog plugins or
accepted claims. Internal task paths and numeric task identifiers are excluded
from public output. The downstream website task may refine selection, wording,
grouping, and presentation while preserving the accepted compatibility
boundaries and source traceability.