# Books Demo Deployment Procedure

Write a repeatable deployment procedure for the Flask/Vue Books demo.

## Requirements checklist

- [ ] Document how to build the application.
- [ ] Document how to run it with configuration supplied through environment variables.
- [ ] Document how to use the health endpoint to verify a deployment.
- [ ] Document how to restore the previous deployment when verification fails.
- [ ] Execute the complete procedure once from a clean checkout.
- [ ] Make no product code changes.

## Questions and decisions

- Which deployment target and operating environment should the procedure support?
- The current checkout has no detected `/health` endpoint and no client build script. How should the procedure satisfy the requested health check and build steps without changing product code?

## Supporting details

- The repository describes a Vue Books page backed by a Flask JSON API.
- `server/app.py` defines `/books` routes but no health route.
- `client/package.json` has a test script but no build or start script.
- `pyproject.toml` declares Flask as the server dependency.
- No deployment manifest, container definition, or deployment target was found in the inspected repository.
- The repository has no `docs/index.md`; `docs/development/documentation.md` says documentation should be placed according to audience and ownership, using the smallest useful structure.

## Implementation plan

Status: Draft

The deliverable is a maintained, user-facing deployment guide for the Books demo, located with the documentation that owns its deployment instructions. The guide should describe only a repeatable path that the repository actually supports. It must cover build and launch commands, environment-variable configuration, health verification, and recovery to the previously deployed version. The procedure must not depend on product code changes. The target platform and the missing build and health capabilities remain unresolved; do not invent commands or claim unsupported behavior. Resolve these constraints before writing operational steps.

Risks include publishing commands that cannot run from a clean checkout or treating an unrelated endpoint as a health check. Keep the blast radius limited to documentation. If the deployment procedure cannot be executed as written or depends on unsupported application behavior, revise or withdraw the guide rather than making product changes under this task. Execute against a clean checkout after drafting; this is the acceptance boundary and should expose missing dependencies, configuration, build steps, and rollback instructions. Determine the intended deployment target first because it controls the available build, environment, health-check, and rollback mechanisms.

### Implementation decisions and open questions

- Deployment target and environment are not specified; obtain that before selecting commands or deployment mechanics.
- The repository does not currently expose a health endpoint or a client production build command. Clarify whether the deployment uses external infrastructure for these capabilities or whether the task must stop until an approved product change is made.
- Keep the user-visible scope to a repeatable deployment guide; no product code changes are authorized.

### Documentation

- Add or update the smallest maintained user-facing documentation location appropriate to the confirmed deployment target.
- Keep the guide's instructions consistent with supported repository behavior and configuration.

### Task checklist

- [ ] Confirm deployment target and resolve build/health capability questions.
- [ ] Inspect the confirmed target's supported deployment, configuration, health-check, and rollback mechanisms.
- [ ] Write the deployment guide with clean-checkout prerequisites, commands, environment configuration, verification, and rollback.
- [ ] Execute the complete guide once from a clean checkout and correct any failures.

### Requirement verification

- Requirements for build, environment-variable configuration, health verification, and rollback are verified by the published guide and its successful end-to-end execution from a clean checkout. That execution must include a failed-verification path that restores the prior deployment.
- The clean-checkout run does not establish behavior on other deployment platforms or environments.
- The no-product-code-change constraint is verified by reviewing the final diff.

### Additional implementation verification

- Record the exact clean-checkout invocation and the verification and rollback outcomes so another operator can repeat the procedure.