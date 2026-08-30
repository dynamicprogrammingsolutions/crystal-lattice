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
- image request/result conversion;
- error envelopes and retryability;
- cancellation before connect, during response, and after completion;
- compatible-profile omission of unsupported fields.

Fixtures assert on request and data structures rather than logs.

### Core/application integration

Use the real public core and application boundaries for:

- ordinary request;
- streaming request;
- tool loop;
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
- base64 image input;
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
- image tool results;
- rate limits/errors where deterministic safe fixtures are insufficient;
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
- Cache controls do not appear on unsupported profiles.
- Credentials and authorization values are absent from logs, errors, sessions,
  notifications, and fixtures.
- Direct provider failures do not select OpenRouter.

## Evidence

Requirement evidence records exact test paths, enabled markers, current user
docs, implementation mappings, active tasks, and final delivery. Manual OAuth
or frontend verification belongs to their owning tasks rather than satisfying
baseline API-key requirements.