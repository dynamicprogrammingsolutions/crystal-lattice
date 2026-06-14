# AWS Static Sites And Docs Deployment

Deploy the Crystal Lattice website and documentation site to AWS, align the docs with the website design, include current plugin docs, generate LLM-accessible docs, and automate deployment through GitHub Actions with narrow AWS credentials.

## Task checklist

- [ ] `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`
- [ ] `tasks/20260614-aws-static-sites-docs-deployment/020-plugin-docs-and-llm-access.md`
- [ ] `tasks/20260614-aws-static-sites-docs-deployment/030-aws-static-hosting-infra.md`
- [ ] `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`
- [ ] `tasks/20260614-aws-static-sites-docs-deployment/050-smoke-test-and-launch.md`

## Context

The requested target architecture is:

- `https://crystallattice.dev` serves the Astro landing site from `landing_page/dist`.
- `https://docs.crystallattice.dev` serves the MkDocs documentation site from `site`.
- Both sites deploy to AWS static hosting using private S3 buckets, CloudFront, ACM certificates, and Route 53 records.
- GitHub Actions should deploy both sites using AWS OIDC and narrowly scoped IAM permissions, not long-lived AWS access keys.

Current repo state:

- The landing site is an Astro static site under `landing_page/`.
- `landing_page/astro.config.mjs:5-10` already sets `site: 'https://crystallattice.dev'`.
- `landing_page/src/components/Nav.astro:12-17` currently links "Docs" to the GitHub README instead of a documentation domain.
- The docs site is MkDocs + Material in `mkdocs.yml`.
- `mkdocs.yml:1-4` currently uses generic `AI Agent Platform` branding and empty `site_url` / `repo_url`.
- `mkdocs.yml:14-29` configures `search` and `mkdocstrings`.
- `docs/requirements.txt:1-4` includes MkDocs, Material, and mkdocstrings dependencies but not LLM docs generation.
- `.github/workflows/publish-docs.yml.disabled:1-53` is an old disabled GitHub Pages workflow and should not be reused as-is for AWS deployment.
- The latest plugin docs live in `plugins/docs/`, not under the MkDocs `docs_dir`.

## Recommended Implementation Order

1. Align website and docs branding/links.
2. Add current plugin docs to the MkDocs build and generate `llms.txt`.
3. Provision AWS static hosting infrastructure.
4. Add GitHub Actions deployment using AWS OIDC.
5. Smoke test the domains, docs, generated LLM files, cache behavior, and workflow.

## Important Decisions Already Made

- Use AWS for both the website and docs site.
- Use separate subdomains/sites rather than trying to host docs under a website subpath.
- Use `docs.crystallattice.dev` for documentation.
- Prefer a build-step copy of `plugins/docs/` into `docs/plugin-development/` over a symlink, because it is more predictable in CI and deployment.
- Prefer Material for MkDocs customization through theme options and `extra_css`, not by importing the Astro/Tailwind global stylesheet.
- Prefer GitHub Actions OIDC to AWS over static AWS access keys.
