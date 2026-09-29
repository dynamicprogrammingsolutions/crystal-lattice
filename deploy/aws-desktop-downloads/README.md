# AWS desktop downloads

Crystal Lattice Desktop uses the existing private S3 and CloudFront download
infrastructure created under `deploy/aws-cli-downloads`. It shares the
production host but uses a separate path:

```text
https://download.crystallattice.dev/crystal-lattice-desktop
```

The desktop GitHub Actions workflow builds, signs, notarizes, and validates a
clean candidate. A later manual publication dispatch references that exact
successful build-only run ID, downloads its retained artifact without
rebuilding, and assumes the existing AWS OIDC role. No long-lived AWS key is
used.

Publication writes only under `crystal-lattice-desktop/`:

```text
Crystal-Lattice-Desktop-v<version>-universal.dmg
Crystal-Lattice-Desktop-v<version>-universal.dmg.sha256
Crystal-Lattice-Desktop-v<version>-release-metadata.json
Crystal-Lattice-Desktop-v<version>-notarization.json
latest.txt
```

Before the first publication, update the existing production stacks:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/up.sh \
  --profile prod \
  --skip-installer-upload

ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/create-github-oidc-role.sh \
  --profile prod

deploy/aws-cli-downloads/configure-github-actions-vars.sh \
  --profile prod \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

The stack update adds desktop cache behaviors and an output for the desktop
prefix. The role update grants the existing release role access to the CLI and
desktop prefixes in the same bucket. The GitHub configuration adds
`DESKTOP_DOWNLOADS_PREFIX` and `DESKTOP_DOWNLOADS_BASE_URL`; it retains the
existing bucket, distribution, region, role secret, and CLI variables.

Preview a local upload without changing AWS:

```bash
deploy/aws-desktop-downloads/publish-assets.sh \
  --assets-dir /path/to/verified-candidate \
  --version 0.9.0 \
  --source-commit <full-commit-sha> \
  --bucket <downloads-bucket> \
  --prefix crystal-lattice-desktop \
  --base-url https://download.crystallattice.dev/crystal-lattice-desktop \
  --distribution-id <distribution-id> \
  --dry-run
```

Smoke-test the public artifact after publication:

```bash
deploy/aws-desktop-downloads/smoke.sh \
  --base-url https://download.crystallattice.dev/crystal-lattice-desktop \
  --version 0.9.0
```

The smoke test downloads the public DMG and checksum, verifies SHA-256, and
checks the accepted notarization and clean-source metadata. Public publication
is irreversible cache-visible state and must follow human approval of the
exact source commit, version, build number, and checksum. The publisher refuses
to overwrite existing versioned desktop objects; partial-publication recovery
therefore requires an explicit inspection and recovery decision.