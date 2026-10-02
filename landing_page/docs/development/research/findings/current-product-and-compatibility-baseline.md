# Current Product and Compatibility Baseline

Status: Accepted research baseline, October 2, 2026.

This finding records current product, provider, configured-profile, feature,
client, and compatibility facts for later website and contributor-facing
work. It is development research, not current public website copy.

Product source revision:
`add5f5e71de3bb1676851bb840dfd77620f63ddb`.

## Outcome

Crystal Lattice is currently best described as a coding-agent workspace that
runs on the user's computer. Its checked-in configuration combines:

- configured-agent compatibility profiles;
- provider and account routes;
- model-family prompt and tool bundles;
- application/session features;
- terminal, HTTP, mobile, desktop, and programmatic clients.

Crystal Lattice compatibility profiles are independent configurations. They
are not the official Codex, Claude Code, Gemini, Qwen, Kimi, Grok, or other
upstream applications, accounts, or sessions.

Provider route, authentication mode, model family, profile tools, and
application-wide features are separate compatibility dimensions. A package
name or selected configuration is not evidence of complete upstream parity,
live account entitlement, or current hosted-provider operation.

## Retained compatibility views

The accepted retained package provides three exhaustive product-oriented
views:

1. **Feature catalog:** 66 plugin projects, including defaults, optional
   packages, distribution-specific packages, examples, fixtures, templates,
   and support libraries.
2. **Provider support:** 10 provider routes across 19 native/provider
   capabilities, including explicit supported, conditional, planned,
   unsupported, not-applicable, and unknown cells.
3. **Model-family features:** 12 profile/tool groups across 21 local,
   provider-native, web, media, MCP, skills, compaction, planning, and
   subagent dimensions.

The human-readable exhaustive review is
[Product Compatibility Matrices](../../../../research/current-product-and-compatibility-baseline/compatibility-matrices.md).
Machine-readable JSON and long-form CSV are retained beside it.

The supporting normalized evidence preserves 20 configured-agent rows,
7 provider/account rows, 33 application-feature rows, and 24 stable claim
records. All of those decision-bearing classifications were accepted by the
user.

## Canonical website draft

A smaller website projection was accepted as a downstream draft:

- 24 complete per-plugin application/session feature rows that avoid provider
  and model-tool duplication and retain each plugin's actual repository path;
- 9 provider rows with 6 selected user-relevant columns;
- 71 current or planned tool rows across Codex-, Claude-, Gemini-, Qwen-,
  Grok-, and Kimi-oriented bundles.

The draft is retained as
[Website Compatibility Data](../../../../research/current-product-and-compatibility-baseline/website-compatibility-data.md)
and
[machine-readable JSON](../../../../research/current-product-and-compatibility-baseline/website-compatibility-data.json).

The downstream website rewrite may refine selection, grouping, wording, and
presentation. It must preserve the accepted identity, status, evidence, and
limitation boundaries.

## Accepted decisions

1. Public and contributor-facing language identifies these as Crystal Lattice
   compatibility profiles and excludes official upstream account/session
   parity.
2. Provider-backed configured profiles without dated real-provider evidence
   default to a partial capability classification.
3. The Codex prompt reference to `update_plan` without a selected
   implementation is a current limitation and contribution gap.
4. The interactive terminal has native session, settings, plugin, history,
   cancellation, reasoning, and tool workflows, but no generic executor for
   every application/session/message action exposed through HTTP.
5. Ollama model identifiers ending in `:cloud` still use the configured local
   Ollama route; account and execution semantics remain unknown without
   provider evidence.
6. Source/test drift and deletion of a historical session whose agent was
   removed from configuration remain explicit limitations.
7. Source and packaging-builder evidence may establish selection while clean
   default loading and produced-artifact execution remain unresolved.
8. Mobile and desktop have production generic consumers, while native UI
   verification remains unknown where the native suites were not run.
9. Provider-reported and locally estimated cost values are transparency data,
   not billing or invoice truth.

## Current product capabilities

The accepted feature baseline includes:

- session search, filtering, titles, pinning, archive/restore, status,
  ordering, message counts, and timestamp metadata;
- copy, fork, deletion, generated-title, summary, snapshot, attachment, and
  history actions at their documented boundaries;
- configurable system messages, request options, provider settings, and
  plugin-contributed controls;
- reasoning, usage, cache, cost, duration, attachment, and provider metadata
  where the selected route supplies or estimates it;
- model-family-specific filesystem, shell, edit, web, media, MCP, skills, and
  compaction behavior;
- synchronous persisted CLI and Python runs plus projected session/message
  reads.

Optional behavior is not presented as default. Message export, Gemini
compaction, provider-independent duration tracking, sleep prevention,
OpenRouter Responses, templates, examples, and embedded-runtime packages keep
their distinct lifecycle states.

## Provider boundaries

- OpenAI Responses supports API-key and saved-ChatGPT routes with materially
  different auth, streaming, flex, prompt-cache retention, cost, and account
  semantics.
- OpenRouter discovers model capabilities and may expose tools, reasoning,
  verbosity, web search, caching, attachments, usage, and image generation,
  but live behavior depends on the selected model and account.
- Direct Anthropic currently provides streaming, tools, reasoning, usage,
  prompt caching, and model discovery. OAuth, cost estimation, server web
  tools, native compaction, fast tiers, image attachments, and Files/PDF
  support remain planned.
- Ollama, Fireworks, Z.ai, and other OpenAI-compatible endpoints use the
  generic reference provider and retain model/endpoint-specific uncertainty.
- OpenRouter image generation is a specialized image route rather than a
  general chat provider.

## Model-family tool boundaries

Current tool surfaces come from the actual package descriptors:

- Codex-oriented: shell variants, apply patch, image viewing, optional MCP,
  and skills.
- Claude-compatible: Bash, file tools, Glob, Grep, web fetch/search,
  background-task stopping, optional MCP, and compatible compaction.
- Gemini-style: file/list/search/edit/shell/web tools.
- Qwen-style: file/list/search/edit/shell/web-fetch tools.
- Grok-style: file viewing/creation, string replacement, and Bash.
- Kimi-style: file/search/edit/shell/web/media tools and compatible
  compaction.

Planned tool rows appear only when backed by maintained work, including
Codex planning/interactive/subagent tools, vendor todo tools, selected MCP and
skills slices, Qwen web search and compaction, Grok unified search, and
Kimi/Gemini child-agent tools.

## Client and execution boundaries

HTTP and the production frontend SDK are the broadest common application
boundary. Mobile and desktop consume generic actions, settings, notifications,
and UI schema through that boundary.

The interactive terminal supports its own substantial workflow but does not
automatically expose every generic HTTP action. Standalone CLI and Python
headless APIs support persisted synchronous requests, continuation, and
projected history; they are not persistent parent-child subagent orchestration.

## Verification

The audit combined deterministic extraction, source/config inspection,
packaging analysis, focused provider/tool/application/client tests, real local
HTTP plus production frontend-adapter tests, and bounded delegated
investigations.

The retained generators validate:

- catalog extraction and accepted review overrides;
- exhaustive matrix completeness and status vocabulary;
- current website tool rows against package descriptors;
- planned website rows against maintained work records;
- provider display cells against the exhaustive provider matrix;
- absence of internal task paths and numeric task identifiers from public
  projection data.

## Remaining limits

The baseline does not establish:

- current hosted-provider/account/model entitlement;
- successful real requests for every configured route;
- native mobile or macOS UI behavior where native suites were not run;
- bundled, optimized, cloud, or embedded produced-artifact execution;
- complete clean-default runtime loading in a fresh cache/environment;
- official upstream session interoperability;
- uniform metadata or exact billing truth across providers.

Those limits must remain visible when a downstream page or compatibility view
depends on them.