# Provider package and documentation

## Package layout

Recommended substantial provider layout:

```text
plugins/<provider-package>/
├── README.md
├── AGENTS.md                     # only for package-specific rules
├── agent_plugin.json
├── pyproject.toml
├── src/<module>/
│   ├── provider.py
│   ├── tools_extension.py
│   ├── reasoning_extension.py
│   └── usage_extension.py
├── tests/
└── docs/
    ├── index.md                  # when README is no longer sufficient
    └── development/
        ├── index.md
        └── specifications/       # when durable target behavior warrants it
```

Use the narrowest file set that remains clear. Do not create empty indexes or
placeholder guides.

## Descriptor

The descriptor lists every provider, extension, feature, tool, or application
entry and its kind. Declare local workspace dependencies explicitly.

The package, descriptor, distribution name, module name, provider ID, and
documentation examples must agree.

## README

Keep the README concise:

- purpose and supported protocol;
- installation/loading;
- first successful request;
- test commands;
- links to detailed user and development docs;
- license.

The first-success example includes a concrete request and expected result.

## User documentation

Document delivered behavior:

- provider selection;
- configuration;
- credential sources;
- model discovery and manual fallback;
- supported extensions;
- compatible endpoints and limitations;
- tools and attachments;
- errors, retries, and cancellation;
- hosted-test prerequisites;
- troubleshooting.

Do not publish target-only features as current behavior.

## Development documentation

For a substantial package, document:

- provider and extension responsibility split;
- native history invariants;
- stream reducer and test seams;
- compatible endpoint configuration, tags, presets, and limitations;
- security/redaction;
- important test commands;
- links to the owning specification.

Implementation pages map code to the specification and do not redefine it.

## Specifications and requirements

Create a package-owned specification when the provider introduces substantial
protocol, compatibility, security, persistence, or phased feature behavior.

Requirements use stable IDs and track implementation, verification,
documentation, and evidence independently.

Provider follow-ups update or refine the owning specification before
implementation when they change the public contract.

## Delivery checklist

- Package imports through normal installation semantics.
- Descriptor entries load and classify correctly.
- Fast deterministic tests pass.
- Application integration passes.
- Required local/hosted tests run with gates enabled.
- Public examples match tests or implementation.
- Credentials are absent from fixtures and output.
- Requirements contain concrete evidence.
- Generated documentation is refreshed only through its maintained source and
  approved generator.