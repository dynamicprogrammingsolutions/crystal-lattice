# Test 28: proportionate small-package documentation

Requirement coverage: `DOCGUIDE-002`, `DOCGUIDE-003`, `DOCVAL-010`

## Purpose

Replace the legacy README-only assertion with a check that a small package
stays small while allowing one justified shared-doc correction.

## Setup

Continue from [Seed 01](seed-01-js-single-file-tool-documentation.md).

## Exact user prompt

> Please implement the documentation improvements identified in the
> investigation. Keep the scope to documentation.

## Expected behavior

The plugin README gains an accurate first-use path. The agent does not create a
package docs tree or placeholder pages. It may update at most one shared plugin
guide when the investigation found a genuinely general single-file authoring
gap; shared text must not turn this plugin's uppercase behavior into a common
contract.

## Mechanical assertions

1. The package README contains the loading form and an input/output example.
2. Changes are limited to that README and at most one shared plugin page.
3. No package-local docs tree or placeholder page is created.
4. Any shared change remains general and does not require other tools to expose
   this plugin's behavior.

## Semantic assessment

Review whether every changed page serves a distinct reader need and whether the
smallest useful structure was chosen.

## Human review

- Was the shared change genuinely general?
- Would README-only have been sufficient?
- Did the result avoid filler?