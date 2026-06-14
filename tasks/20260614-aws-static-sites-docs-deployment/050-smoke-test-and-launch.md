# Smoke Test And Launch

Verify the deployed website and docs site end to end after AWS infrastructure and GitHub Actions deployment are in place.

## Requirements checklist

- [ ] Confirm website loads at `https://crystallattice.dev`.
- [ ] Confirm docs load at `https://docs.crystallattice.dev`.
- [ ] Confirm docs are reachable from the website nav and CTA links.
- [ ] Confirm plugin docs are present in the docs nav.
- [ ] Confirm `https://docs.crystallattice.dev/llms.txt` is generated and useful.
- [ ] Confirm `llms-full.txt` if configured.
- [ ] Confirm HTTPS, redirects, cache behavior, and CloudFront invalidations.
- [ ] Confirm GitHub Actions manual deploy succeeds.
- [ ] Document remaining launch notes or follow-up improvements.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`

## Smoke Test Checklist

Website:

- Open `https://crystallattice.dev`.
- Test desktop and mobile widths.
- Test dark/light behavior if present.
- Open `/mobile`, `/privacy`, and `/terms`.
- Click the Docs nav link and confirm it opens `https://docs.crystallattice.dev/`.
- Confirm GitHub links still point to the repository.

Docs:

- Open `https://docs.crystallattice.dev`.
- Confirm title/branding says Crystal Lattice Docs.
- Confirm logo/favicon render.
- Toggle light/dark docs palette.
- Navigate to Overview, Guides, Current Plugin Docs, and Reference.
- Confirm copied plugin docs render, especially `plugin-development/index.md`, provider docs, tool docs, config schema, UI elements, and testing docs.
- Confirm mkdocstrings-generated API pages render.

LLM access:

- Open `https://docs.crystallattice.dev/llms.txt`.
- Confirm it includes docs URLs and descriptions rather than only raw navigation noise.
- If configured, open `https://docs.crystallattice.dev/llms-full.txt`.
- Confirm no secrets, deployment credentials, or private-only operational details are exposed.

AWS:

- Confirm both domains use valid TLS certificates.
- Confirm Route 53 records point to CloudFront aliases.
- Confirm S3 buckets remain private.
- Confirm CloudFront invalidations are created after deployment.
- Confirm cache headers are acceptable for HTML and static assets.

GitHub Actions:

- Run the deployment workflow manually.
- Confirm OIDC role assumption succeeds.
- Confirm both S3 sync commands complete.
- Confirm both CloudFront invalidations complete or are created successfully.

## Completion Notes To Add Later

When completing this task, append:

- deployed domains
- AWS bucket names
- CloudFront distribution IDs
- workflow run URL
- any known cache/header caveats
- any docs pages intentionally excluded from `llms.txt`
