# Add Restricted Python Execution Tool

Expose a deliberately restricted Python interpreter as a tool for calculations
without letting generated code change the application, runtime,
configuration, plugin catalog, credentials, or workspace.

## Requirements checklist

- [ ] The embedded agent exposes one fixed restricted-Python tool contract.
- [ ] Executed code has no application/runtime/plugin/configuration mutation
  APIs and no package installation.
- [ ] The initial interpreter surface has an explicit syntax, builtin, and
  module allowlist.
- [ ] Network, arbitrary filesystem, process, native bridge, and credential
  access are unavailable.
- [ ] Execution has bounded time, work, and output with a recoverable tool
  error on limit or policy violation.
- [ ] The real mobile app visibly renders submitted code and its bounded result
  during a simple multi-round model request.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md

## Scope notes

This task has no approved execution plan. It will select a restricted
interpreter design only after the embedded CPython host and lifecycle behavior
are measured.

The tool is not a general shell, subprocess runner, package environment, or
security claim about unrestricted same-process `exec`. It may accept copied
inputs and return bounded structured output, but workspace access remains
owned by the separate `Read` and `Write` tools.