# Session and message data query

This target specification defines a consistent way to enumerate session
summaries, retrieve canonical message ranges, apply plugin-declared session
filters, and reduce returned JSON with caller-supplied RFC 9535 JSONPath
include and exclude selectors.

It covers:

- direct Python access through the local application runtime;
- one-shot `crystal-lattice sessions` and `crystal-lattice messages`
  commands;
- existing HTTP session and message collection envelopes;
- frontend SDK adoption and lazy field hydration;
- plugin-driven date filtering;
- lossless JSON and line-oriented text, TSV, and CSV output;
- backward compatibility when no include or exclude selector is supplied;
- generic conditional selection without a fixed message-role registry;
- bounded projection complexity and actionable failures.

The specification deliberately provides low-level enumeration and projection
instead of a product-specific search language. Shell users may chain one
session ID per line into per-session message commands and search their
line-oriented output with tools such as `grep`. Python and frontend callers
may compose richer searches over the same projected data.

Current implementation and evidence state is tracked in
[requirements.md](requirements.md). The specification is a target; current
user documentation continues to describe only delivered behavior.

## Specification documents

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Related specifications

- [Application session listing](../../../../../../core/python/docs/development/specifications/session-listing/index.md)
- [Local headless agent runs](../headless-agent-runs/index.md)
- [CLI distribution verification](../cli-distribution/index.md)

## Affected current documentation

- [Local headless agent runs](../../../headless-agent-runs.md)
- [Application runtime development](../../index.md)
- [Plugin UI elements](../../../../../../plugins/docs/ui-elements.md)
- [Frontend SDK](../../../../../../packages/frontend-sdk/README.md)