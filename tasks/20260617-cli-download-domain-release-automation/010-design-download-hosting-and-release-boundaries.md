# Design Download Hosting And Release Boundaries

Define the CLI download hosting architecture, test/prod domain profiles, release responsibilities, script responsibilities, GitHub workflow boundaries, and expected developer UX before implementation.

## Requirements checklist

- [x] Confirm exact testing download FQDN and production download FQDN.
- [x] Confirm whether production downloads use `crystallattice.dev` or `download.crystallattice.dev`.
- [x] Define test/prod profile defaults for stack names, hosted zones, domains, bucket prefixes, and URL paths.
- [x] Define the required S3 object layout and URL layout.
- [x] Define which scripts provision infrastructure, upload installer, publish existing assets, promote GitHub releases, and orchestrate release tags.
- [x] Document that GitHub Actions matrix builds official platform artifacts.
- [x] Document that local scripts do not locally build all release artifacts.
- [x] Define GitHub repository variables/secrets needed by the release workflow.
- [x] Define test-domain validation steps that every later task should use.
- [x] Add implementation notes and decisions to `deploy/aws-cli-downloads/README.md` during implementation.
- [x] Test documentation examples against the testing domain before marking this task complete.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

## Release Boundary

Official platform artifacts are built by `.github/workflows/release-crystal-lattice-cli.yml` using a matrix:

```text
linux-amd64
darwin-amd64
darwin-arm64
windows-amd64
```

Local scripts must not claim to build these all locally. They may:

- validate local version/tag state
- provision download infrastructure
- upload a domain-specific installer
- configure GitHub Actions variables and secrets
- push release tags
- watch GitHub Actions runs
- publish already-built artifacts from a local directory
- download/promote existing GitHub Release assets
- smoke-test a public download URL

## URL Layout

The download base URL should contain:

```text
<base-url>/install.sh
<base-url>/latest.txt
<base-url>/crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-darwin-amd64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-darwin-arm64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-windows-amd64.zip
```

Current path convention:

```text
/crystal-lattice-cli
```

The scripts should keep the prefix configurable, defaulting to `crystal-lattice-cli`.

## Profile Defaults To Decide

Suggested testing profile:

```text
profile: test
region: us-east-1
stack: crystal-lattice-cli-downloads-test
hosted zone: dynamicprogrammingsolutions.com
download domain: download.crystallattice.dev.dynamicprogrammingsolutions.com
prefix: crystal-lattice-cli
bucket prefix: crystal-lattice-cli-downloads-test
```

Production profile:

```text
profile: prod
region: us-east-1
stack: crystal-lattice-cli-downloads-prod
hosted zone: crystallattice.dev
download domain: download.crystallattice.dev
prefix: crystal-lattice-cli
bucket prefix: crystal-lattice-cli-downloads-prod
```

The user confirmed the production download host should be `download.crystallattice.dev`.

## Documentation Requirements

`deploy/aws-cli-downloads/README.md` must include:

- architecture summary
- what `up.sh` does and does not do
- ready-to-use test-domain commands
- ready-to-use production-domain commands
- GitHub OIDC setup
- GitHub variables/secrets setup
- release workflow trigger/watching
- manual publish of existing local assets
- promotion of GitHub Release assets to test/prod
- smoke testing
- test-to-production cutover
- teardown

## Testing Requirements

Before this design task is considered done:

- validate the selected testing hosted zone exists with AWS CLI
- verify the planned test domain can be represented as a Route 53 record in the selected zone
- run `--help` for every new script once it exists
- run documentation examples in dry-run mode where supported
- update this task with any domain/profile decision changes

## Completion Notes

Added during completion on 2026-06-18.

The implementation uses `download.crystallattice.dev.dynamicprogrammingsolutions.com` for the testing profile and `download.crystallattice.dev` for the production profile default. The download path prefix defaults to `crystal-lattice-cli`, so the testing base URL is:

```text
https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
```

The production host decision has been confirmed as `download.crystallattice.dev`.
