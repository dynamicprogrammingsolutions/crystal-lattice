# Anthropic provider verification

## Verification layers

### Deterministic contract tests

Use local fake HTTP/SSE fixtures for:

- API-key precedence and fallback;
- header redaction;
- model discovery and capability normalization;
- ordinary native conversion;
- content-block streaming;
- partial tool JSON;
- thinking, redacted thinking, and signatures;
- initial/final usage;
- cache request shaping;
- safe SDK error messages and provider-owned retry behavior;
- cancellation before connect, during response, and after completion;
- compatible-profile omission of unsupported fields.

Fixtures assert on request and data structures rather than logs.

### Core/application integration

Use the real public core and application boundaries for:

- ordinary request;
- streaming request;
- tool loop;
- usage formatting and turn/session totals;
- duration/TPS interoperability;
- persistence and reload;
- cancellation event;
- stable error event;
- plugin discovery/config loading;
- operation with individual extensions disabled.

### Local Ollama compatibility

Run with the Anthropic-compatible endpoint and a selected local model:

- `/v1/models` discovery;
- ordinary text;
- streaming text;
- tools and tool results;
- thinking/reasoning;
- usage;
- effort-level acceptance and behavioral effect where the selected model
  permits a stable comparison;
- cancellation where the endpoint and client permit it;
- omission of caching, PDF, citation, request-metadata, token-count, and
  unsupported tool-choice fields.

Tests use `integration` and `ollama` markers. A skipped gated test is not a
successful verification run unless the gate was enabled and the skip is
expected for the selected model.

### Hosted Anthropic verification

Selective hosted tests cover behavior unavailable through Ollama:

- official model discovery and capabilities;
- API-key authentication failures;
- ordinary and streaming requests;
- complete Claude tool loop;
- adaptive/extended thinking and signature continuity;
- automatic and one-hour prompt caching;
- cache-read and cache-creation usage;
- selectable cache TTL;
- safe SDK rate-limit/error detail and provider-owned retries where
  deterministic fixtures are insufficient;
- cancellation against a real stream.

Hosted tests use `integration`, `api`, and `anthropic` markers and document
credential and cost requirements.

## Standard assertions

- Stream partials are chunk-local.
- Final visible text equals the provider final text, not a double-accumulated
  stream.
- Native history contains completed messages and no raw chunks.
- Tool IDs survive execution and reload.
- Tool schemas and calls use the active request-bound interop registry.
- Thinking block order and signatures survive tool rounds.
- Usage remains correct when fields arrive at different stream phases.
- Duration/TPS derives from the standard turn-cumulative usage fields.
- Cache controls do not appear on unsupported profiles.
- Credentials and authorization values are absent from logs, errors, sessions,
  notifications, and fixtures.
- Direct provider failures do not select OpenRouter.

## Evidence

Requirement evidence records exact test paths, enabled markers, current user
docs, implementation mappings, active tasks, and final delivery. Manual OAuth
or frontend verification belongs to their owning tasks rather than satisfying
baseline API-key requirements.