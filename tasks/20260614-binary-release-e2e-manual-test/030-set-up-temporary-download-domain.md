# Set Up Temporary Download Domain

Set up a temporary custom download domain under `dynamicprogrammingsolutions.com` for release installer testing.

## Requirements checklist

- [ ] Confirm Route 53 hosted zone access for `dynamicprogrammingsolutions.com`.
- [ ] Confirm that `downloads.crystallattice.dev.dynamicprogrammingsolutions.com` is acceptable.
- [ ] Create or identify an ACM certificate in `us-east-1`.
- [ ] Create a CloudFront distribution in front of the release S3 bucket.
- [ ] Configure the custom domain on CloudFront.
- [ ] Add the Route 53 alias record.
- [ ] Verify `install.sh` is available through the custom domain.
- [ ] Verify `latest.txt` is available through the custom domain.
- [ ] Verify at least one archive downloads through the custom domain.
- [ ] Record all AWS CLI commands used.
- [ ] Record teardown commands or cleanup notes.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On: `tasks/20260614-binary-release-e2e-manual-test/010-define-manual-test-matrix.md`

## Domain

Preferred temporary domain:

```text
downloads.crystallattice.dev.dynamicprogrammingsolutions.com
```

This number of labels is valid DNS as long as each label is within DNS length limits. The labels here are comfortably below those limits.

Future intended domain:

```text
crystallattice.dev
```

## Current Download Source

The current public S3 base is:

```text
https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli
```

The current S3 bucket/prefix used by the workflow:

```text
s3://crystal-lattice-downloads-874087778966/crystal-lattice-cli/*
```

The workflow publishes with:

```bash
python scripts/publish_crystal_lattice_s3.py \
  --assets-dir release-assets \
  --bucket crystal-lattice-downloads-874087778966 \
  --prefix crystal-lattice-cli \
  --region us-east-1
```

## Recommended AWS Shape

Prefer this architecture:

```text
Route 53 alias
  -> CloudFront distribution
    -> S3 release bucket origin
```

Use CloudFront rather than an S3 website endpoint so HTTPS and a custom certificate work cleanly.

Prefer CloudFront Origin Access Control if making the S3 bucket private is in scope. If this task is only a temporary validation step, a public S3 origin behind CloudFront is acceptable, but record that decision.

## AWS CLI Work To Capture

Capture concrete commands for:

- hosted zone lookup
- ACM certificate request or discovery
- DNS validation record creation if needed
- CloudFront distribution creation
- CloudFront custom alias and certificate attachment
- Route 53 alias record creation
- verification with `curl`

Example verification commands:

```bash
DOWNLOAD_BASE_URL="https://downloads.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli"

curl -fsSI "$DOWNLOAD_BASE_URL/install.sh"
curl -fsSL "$DOWNLOAD_BASE_URL/latest.txt"
curl -fL "$DOWNLOAD_BASE_URL/crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz" -o /tmp/crystal-lattice-linux.tar.gz
```

## Installer Implication

Hosting `install.sh` at the custom domain is not enough if the script still defaults to the old S3 base. During testing, either:

1. Run the installer with:

   ```bash
   CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL"
   ```

2. Or update `scripts/install.sh` `DEFAULT_DOWNLOAD_BASE_URL` and publish that installer.

For temporary testing, prefer the environment-variable override unless the task explicitly decides to test the final branded default URL.
