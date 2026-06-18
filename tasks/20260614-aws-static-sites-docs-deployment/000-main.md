# AWS Static Sites And Docs Deployment

Deploy the Crystal Lattice website and documentation site to AWS, align the docs with the website design, include current plugin docs, generate LLM-accessible docs, and automate deployment through GitHub Actions with narrow AWS credentials.

## Task checklist

- [x] `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`
- [x] `tasks/20260614-aws-static-sites-docs-deployment/020-plugin-docs-and-llm-access.md`
- [x] `tasks/20260614-aws-static-sites-docs-deployment/025-docs-content-cleanup.md`
- [x] `tasks/20260614-aws-static-sites-docs-deployment/030-aws-static-hosting-infra.md`
- [x] `tasks/20260614-aws-static-sites-docs-deployment/035-docs-site-layout-cleanup.md`
  - BLOCKS `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`
- [x] `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`
- [ ] `tasks/20260614-aws-static-sites-docs-deployment/050-smoke-test-and-launch.md`

## Context

The requested initial testing architecture is:

- `https://crystallattice.dev.dynamicprogrammingsolutions.com` serves the Astro landing site from `landing_page/dist`.
- `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com` serves the MkDocs documentation site from `docs_site/dist`.
- Both sites deploy to AWS static hosting using private S3 buckets, CloudFront, ACM certificates, and Route 53 records.
- GitHub Actions should deploy both sites using AWS OIDC and narrowly scoped IAM permissions, not long-lived AWS access keys.
- The final planned domains remain `https://crystallattice.dev` and `https://docs.crystallattice.dev`, but those should be switched only after testing is complete.

Current repo state:

- The landing site is an Astro static site under `landing_page/`.
- `landing_page/astro.config.mjs:5-10` currently sets `site: 'https://crystallattice.dev'`; for the testing phase, use `https://crystallattice.dev.dynamicprogrammingsolutions.com`.
- `landing_page/src/components/Nav.astro:12-17` currently links "Docs" to the GitHub README instead of a documentation domain.
- The docs site is MkDocs + Material configured in `docs_site/mkdocs.yml`.
- `docs_site/mkdocs.yml` uses Crystal Lattice branding, dynamic public URL env vars, Material theme customization, `search`, `mkdocstrings`, and `mkdocs-llmstxt`.
- `docs_site/requirements.txt` includes MkDocs, Material, mkdocstrings, and LLM docs generation dependencies.
- `docs_site/scripts/build_mkdocs_site.py` prepares MkDocs inputs, builds `docs_site/dist`, and refreshes generated reference Markdown under `docs/reference/`.
- `.github/workflows/publish-docs.yml.disabled:1-53` is an old disabled GitHub Pages workflow and should not be reused as-is for AWS deployment.
- The latest plugin docs live in `plugins/docs/`, not under the MkDocs `docs_dir`.

## Recommended Implementation Order

1. Align website and docs branding/links.
2. Add current plugin docs to the MkDocs build and generate `llms.txt`.
3. Clean up docs content so the published site contains Crystal Lattice product/docs content rather than internal planning or obsolete prompt/tool artifacts.
4. Provision AWS static hosting infrastructure.
5. Clean up docs-site layout before automating deploys.
6. Add GitHub Actions deployment using AWS OIDC.
7. Smoke test the domains, docs, generated LLM files, cache behavior, and workflow.

## Important Decisions Already Made

- Use AWS for both the website and docs site.
- Use separate subdomains/sites rather than trying to host docs under a website subpath.
- Use `docs.crystallattice.dev.dynamicprogrammingsolutions.com` for documentation during testing, then later switch to `docs.crystallattice.dev`.
- Use `crystallattice.dev.dynamicprogrammingsolutions.com` for the main website during testing, then later switch to `crystallattice.dev`.
- Prefer a build-step copy of `plugins/docs/` into `docs/plugin-development/` over a symlink, because it is more predictable in CI and deployment.
- Prefer Material for MkDocs customization through theme options and `extra_css`, not by importing the Astro/Tailwind global stylesheet.
- Prefer GitHub Actions OIDC to AWS over static AWS access keys.
- Keep authored docs under `docs/`, MkDocs-specific source overlays under `docs_site/source/`, prepared MkDocs input under `docs_site/prepared/`, final docs build output under `docs_site/dist/`, and generated reference Markdown snapshots under `docs/reference/`.
