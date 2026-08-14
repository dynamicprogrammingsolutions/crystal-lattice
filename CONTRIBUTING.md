# Contributing To Crystal Lattice

Crystal Lattice is an early-stage project spanning Python, React Native,
TypeScript, Elixir, deployment tooling, documentation, and first-party plugins.
Focused fixes, tests, documentation improvements, and well-scoped feature
proposals are welcome.

## Before You Start

Choose the narrowest package or subsystem that owns the behavior. Start with
its README and public development documentation:

- [Development documentation](docs/development/index.md)
- [Architecture](ARCHITECTURE.md)
- [Core and application development](DEVELOPMENT.md)
- [Plugin authoring](plugins/docs/index.md)
- [Terminal/server application](application/python/README.md)
- [React Native mobile application](mobile/crystal-lattice-control-rn/README.md)
- [Bridge service](bridge-elixir/README.md)

Search existing issues before opening a duplicate. A prior issue is useful for
large or user-visible changes, but it is not required for a small, focused fix.

## Development Setup

Crystal Lattice requires Python 3.10 or newer for the Python packages.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

Install only the first-party plugin packages you are changing:

```bash
python -m pip install -e "plugins/<plugin-name>[dev]"
```

For shared frontend packages, install the root npm workspace:

```bash
npm install
```

The mobile and desktop applications have their own native setup. Follow their
package READMEs and install dependencies from the application directory. The
mobile application requires Node.js 20 or newer.

The landing site uses Yarn:

```bash
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
```

Other services, including the Elixir bridge and cloud orchestrator, document
their prerequisites and development commands in their own READMEs.

## Tests And Documentation

Run focused tests for the boundary you changed before broad suites. Common fast
Python checks include:

```bash
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
pytest plugins/<plugin-name>/tests -q
```

Shared frontend package checks include:

```bash
npm --workspace @crystal-lattice/frontend-sdk test
npm --workspace @crystal-lattice/frontend-sdk-react test
npm --workspace @crystal-lattice/frontend-rn-components test
```

Use package-local commands for mobile, desktop, bridge, cloud, landing-page, and
documentation changes. Integration, hosted-API, Docker, and native end-to-end
tests should be run when the changed behavior crosses those boundaries; they
are not expected for unrelated changes.

Add or update tests for public behavior and bug fixes. Update the documentation
owned by the changed package when installation, configuration, APIs, supported
behavior, or contributor workflow changes. Do not edit generated documentation
trees directly.

## Required Pull Request Checks

Public pull requests run four credential-free checks:

- `Public CI / Repository checks`
- `Public CI / Python unit tests`
- `Public CI / Frontend package tests`
- `Public CI / Landing and docs build`

Run the relevant commands locally before opening a pull request.

Repository and workflow checks:

```bash
git diff --check
actionlint .github/workflows/*.yml
python scripts/check_github_actions_security.py
```

Python unit tests:

```bash
python -m pip install \
  -e "core/python[dev]" \
  -e application/python \
  -e "plugins/openai_responses[dev]" \
  -e plugins/tool-compat-shared \
  -e plugins/mcp-shared \
  -e plugins/web-fetch-shared
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
```

Shared frontend package tests:

```bash
npm ci
npm --workspace @crystal-lattice/frontend-sdk test
npm --workspace @crystal-lattice/frontend-sdk-react test
npm --workspace @crystal-lattice/frontend-rn-components test
```

Landing and documentation builds:

```bash
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Required public CI intentionally excludes hosted-provider tests, Docker/cloud
integration, mobile/desktop native builds, native UI tests, signing, TestFlight,
and deployment. Those checks still apply when a change crosses their boundary;
run and report them explicitly rather than treating their absence from required
CI as evidence that they are unnecessary.

## Pull Requests

Keep pull requests focused enough to review and validate. In the description:

- explain the outcome and affected boundary;
- link the relevant issue when one exists;
- list the tests and manual checks actually performed;
- identify public documentation, compatibility, security, privacy, deployment,
  or data-migration effects;
- call out meaningful deferred work or known limitations.

Do not claim that a skipped or gated test passed. Avoid unrelated formatting,
generated output, or cleanup in the same pull request.

## Sensitive And Local Data

Never commit credentials, tokens, private keys, personal data, private
conversations, runtime session data, unnormalized captured logs, local user
paths, build caches, or other machine-specific artifacts.

Sanitize logs and screenshots before attaching them to issues or pull requests.
If you discover a possible vulnerability or exposed credential, follow
[SECURITY.md](SECURITY.md) instead of opening a public issue.

## Contribution License

Contributions are accepted under the license that applies to the file or
subtree being changed. Most original Crystal Lattice material is Apache-2.0,
while more specific license and notice files may apply within a subtree. See
[LICENSE](LICENSE) and [LICENSING.md](LICENSING.md) before contributing.

By intentionally submitting a contribution for inclusion, you agree that it
may be distributed under the applicable project or subtree license. The project
does not currently require a separate contributor license agreement or
Developer Certificate of Origin signoff.

## Participation

Be respectful, constructive, and specific. Assume good faith, discuss the
technical or user outcome rather than the person, and make space for maintainers
and contributors with different levels of familiarity with the repository.