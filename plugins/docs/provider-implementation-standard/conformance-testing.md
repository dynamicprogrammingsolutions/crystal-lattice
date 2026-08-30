# Provider conformance testing

## Deterministic package tests

Cover the provider without network credentials:

- config normalization;
- credential precedence;
- request URL, headers, and payload;
- secret redaction;
- model discovery success, malformed data, and failure;
- core/native conversion;
- single-message conversion;
- ordinary finalization;
- every known stream event;
- chunk-local partials;
- premature stream termination;
- full native history;
- cancellation lifecycle;
- provider error categories;
- compatibility profiles and overrides.

Each provider extension covers:

- config and UI;
- tags and capability gating;
- request shaping;
- streaming accumulation;
- final metadata;
- disabled and unsupported behavior;
- interaction with the shared accumulator;
- operation without unrelated extensions.

Usage-capable providers additionally cover:

- normalized and formatted usage;
- tool-turn and session cumulative totals;
- persistence/rebuild;
- duration/TPS interoperability;
- reported-versus-estimated provenance;
- pricing-catalog and cached-token estimation behavior when supported.

## Tool-loop tests

For tool-capable providers, cover:

- schema conversion through request context;
- emitted call inspection;
- partial arguments;
- invalid argument sanitization;
- tool execution;
- provider-native tool results;
- multimodal results where supported;
- follow-up request;
- persistence/reload;
- display metadata.

Use at least one real tool consumer rather than testing only private helpers.

## Application integration

Exercise the public application/core boundary for:

- ordinary request;
- streaming request;
- tool-enabled request;
- cancellation;
- error event;
- config loading and plugin discovery;
- persisted native history when material.

Direct route-function calls do not count as HTTP integration, and mocked
frontend tests do not count as backend integration.

## Local-compatible profile

When the protocol has a practical local implementation:

- provide explicit environment/config helpers;
- check endpoint and selected model availability;
- run with the correct integration/provider markers;
- test the documented supported subset;
- test omission of unsupported features.

A skip without enabling the required gate is reported as not run.

## Hosted verification

Use selective hosted tests for:

- authentication;
- official model discovery;
- protocol behavior unavailable locally;
- billing/rate-limit headers where safe;
- provider-specific caching, server tools, or continuation state;
- real cancellation.

Mark credentials, provider, cost, latency, and manual requirements. Prefer one
focused model per capability instead of a broad expensive matrix.

## Native-history tests

Reload the session through a new core/application instance and verify:

- opaque provider state survives;
- tool IDs and results remain linked;
- reasoning state remains valid;
- attachment references remain usable;
- the next request completes.

## Acceptance of a provider profile

A profile is accepted only when:

- required tests are collected;
- commands exit successfully;
- no teardown/open-handle error remains;
- requested gated tests actually ran;
- evidence is recorded in package requirements or delivery notes.