# Anthropic compatibility profiles

## Purpose

The `anthropic` provider supports the official Anthropic API and selected
Anthropic-compatible endpoints through one transport and native-message model.
Profiles describe verified differences without forking the provider or
pretending every endpoint is feature-complete.

## Profile model

A profile supplies conservative defaults for:

- authentication header style;
- Messages and model-discovery paths;
- API version and beta headers;
- streaming event support;
- tool schema/call/result behavior;
- tool-choice controls;
- thinking mode and signature behavior;
- prompt caching and retention;
- image source types;
- request metadata;
- usage timing and fields;
- model capability metadata;
- error envelope behavior.

Explicit configuration may override a documented profile capability. An
override is visible in effective configuration and testable. Unknown endpoints
start from conservative defaults.

## `official-anthropic`

The official profile:

- uses API-key authentication from resolved config;
- sends the required Anthropic API version;
- uses `/v1/messages` and `/v1/models`;
- consumes published model capabilities;
- supports the baseline tool, reasoning, usage, caching, and image extension
  contracts when the selected model advertises them;
- preserves provider request IDs and error types;
- enables automatic prompt caching by default.

OAuth refines authentication and headers later without changing the native
Messages profile.

## `ollama`

The local Ollama profile targets its Anthropic-compatible API.

Baseline expected support:

- ordinary messages;
- streaming content-block events;
- system prompts and multi-turn history;
- tool calls and tool results;
- thinking/reasoning;
- base64 image input;
- input/output usage;
- model IDs through `/v1/models`.

Unsupported or disabled by default:

- prompt caching;
- one-hour cache retention;
- PDFs and document blocks;
- citations;
- token counting;
- request metadata;
- forced/disabled named tool choice;
- mid-stream Anthropic error events;
- URL image sources.

Thinking-budget acceptance does not imply enforcement. The profile does not
claim a capability solely because the endpoint tolerates its request field.

## `custom`

The custom profile begins with:

- ordinary Messages transport;
- text streaming;
- no optional features;
- configured auth and headers;
- optional `/v1/models` discovery.

Users enable optional behavior through explicit compatibility overrides.
Package docs must warn that overrides can cause provider validation failures.

## Capability precedence

Effective support is resolved in this order:

1. explicit compatibility override;
2. published model capability from the official model response;
3. selected named profile;
4. conservative disabled/default behavior.

An explicit disable always wins. A published capability does not override an
endpoint-level incompatibility.

## Model discovery response compatibility

The provider accepts:

- official Anthropic model data with capability fields;
- OpenAI-style `data` arrays containing model IDs and optional names.

Missing capabilities produce no optional feature tags. Discovery failure
returns an empty list so users can enter a model ID manually.

## Testing profiles

- `messages-basic`: ordinary, streaming, system, multi-turn, stop/error.
- `messages-agent`: tools/results, reasoning, usage, cancellation, images.
- `anthropic-cache`: automatic/explicit caching and cache usage.
- `official-anthropic`: official discovery and baseline feature capability
  gating.
- `compatible-local`: Ollama-supported subset and explicit omission tests.

Hosted compatible profiles may be added only with real public behavior and
package-local tests.