# Books demo deployment runbook

Create a repeatable deployment runbook for the Flask/Vue Books demo. The
runbook is for an operator starting from a clean checkout and must cover the
full deployment lifecycle, including verification and recovery. This task is
documentation-only: do not change product code, application routes, client
code, or deployment behavior while completing it.

## Requirements checklist

- [ ] The maintained documentation describes the prerequisites and exact
  commands for building the application from a clean checkout, including
  dependency installation, the build output or served artifact, and the
  expected working-directory assumptions.
- [ ] The maintained documentation explains how to start the deployed
  application with configuration supplied through environment variables. It
  names each required variable, its source/default where applicable, how the
  Flask API and Vue client receive their configuration, and which values must
  not be committed or printed.
- [ ] The maintained documentation defines deployment verification through an
  approved health endpoint: URL, request, expected response/status, timeout or
  retry behavior, and explicit pass/fail criteria are included.
- [ ] The maintained documentation defines rollback when verification fails,
  including how the previous deployment is identified and retained, how the
  active revision/artifact is switched back, how the service is restarted or
  traffic is restored, and how the rollback itself is verified with the
  health check.
- [ ] The procedure is repeatable from a clean checkout and includes an
  end-to-end acceptance record showing one successful execution of build,
  configuration, start, health verification, induced or observed failure
  handling as applicable, and rollback to the previous deployment. The record
  identifies the checkout/revision, commands, environment-variable
  conventions, and observed results without exposing secrets.
- [ ] The runbook states any prerequisite outside the repository, deployment
  target assumptions, data-persistence implications, and operator stop
  conditions needed to execute it safely. Unsupported behavior is marked
  `Not implemented` or called out as a blocker rather than invented.
- [ ] No product code, application configuration source, client source, or
  deployment runtime behavior is changed as part of this task.

## Research and supporting facts

- The repository root has a short `README.md` but no deployment guide or
  deployment manifest.
- The Flask application is `server.app:app`; `pyproject.toml` declares Flask
  as its only Python dependency.
- The API currently exposes `GET /books` and book mutation routes. There is no
  dedicated health route in `server/app.py`.
- `client/package.json` declares only a Vitest test script; it does not declare
  a production build script or a bundler, and the client HTTP base URL is
  currently hard-coded to `http://localhost:5000` in `client/src/http.js`.
- The current test suite verifies basic API responses and Vue rendering, but
  it does not verify a built artifact, a deployed process, environment
  configuration, health probing, or rollback.
- The repository ignores dependency/cache outputs such as `node_modules/`,
  `.pytest_cache/`, and `__pycache__/`; a clean-checkout acceptance should
  install dependencies explicitly and avoid relying on ignored state.

## Unresolved requirement questions

- Which deployment target and process manager are in scope for the runbook?
  The repository does not identify a hosting provider, container runtime,
  reverse proxy, or release directory convention.
- Which endpoint is approved as the deployment health endpoint? A dedicated
  `/health` endpoint is not present, and selecting `/books` as a health probe
  would be a contract decision that should be explicit.
- Where does the “previous deployment” live, and what rollback mechanism is
  available on the target (immutable release directories, image tags, package
  versions, or another mechanism)?
- Is the intended acceptance allowed to use a local deployment harness that
  represents the target process, or must it run against a particular hosted
  environment?

## Execution plan

Status: Draft

The runbook should be owned by the deployment/operator-facing documentation
area. It should present one linear procedure with explicit inputs and
decision points: prepare an exact revision, install dependencies, build the
deployable artifact, export environment configuration, start or promote the
release, probe the approved health endpoint, and either declare success or
restore the previous release. The procedure must distinguish facts supported
by this checkout from target-specific prerequisites and must not imply that
the missing client build or health route already exists.

The acceptance evidence should cross the real deployment boundary selected for
the task. A unit test or mocked HTTP request is not sufficient. The operator
should execute the documented commands once from a fresh checkout, capture
the revision and non-secret configuration inputs, confirm the health response
against the running deployment, and demonstrate the rollback path or record
the exact blocker if the selected target cannot safely exercise it. The final
documentation should preserve the command transcript/result summary as
evidence without storing credentials.

### Implementation decisions and open questions

- Keep this change documentation-only; no missing build script, environment
  adapter, health route, or deployment automation may be added under this
  task.
- Resolve the deployment target, health probe, and previous-release mechanism
  before writing target-specific commands. If they remain unspecified, write
  the supported local procedure and visibly mark target-dependent sections
  `Not implemented` rather than selecting an unapproved contract.
- Treat the absence of a declared Vue production build and dedicated health
  endpoint as a release-blocking fact for any procedure that claims to deploy
  those components. Do not substitute a mock or test-only shortcut.

### Documentation

- Update or add the smallest maintained operator-facing documentation page
  that owns deployment guidance; do not create placeholder documentation
  structures.
- Include prerequisites, clean-checkout build steps, environment-variable
  table, start/promote steps, health verification, rollback, failure
  handling, and the dated end-to-end acceptance record.
- Link the runbook from the nearest maintained documentation index if one
  exists and the link is appropriate for its audience.

### Task checklist

- [ ] Confirm the deployment target, process manager, approved health endpoint,
  and previous-release/rollback mechanism.
- [ ] Inspect the selected target's supported build and runtime commands
  without changing product code.
- [ ] Draft the operator runbook with explicit variables, artifacts,
  verification criteria, rollback steps, and stop conditions.
- [ ] Execute the documented procedure once from a clean checkout and record
  the revision, non-secret inputs, commands, and results.
- [ ] Review the runbook against the actual execution and correct unsupported
  or ambiguous instructions.
- [ ] Run documentation/link checks applicable to the selected documentation
  location and confirm no product files changed.

### Requirement verification

- The build requirement is verified by following the documented build commands
  from a fresh checkout and confirming the stated artifact or serving
  behavior; inspection alone is insufficient.
- The environment-configuration requirement is verified by starting the real
  deployment process with the documented environment variables and observing
  that it binds to and calls the configured components without hard-coded
  local-only assumptions.
- The health-verification requirement is verified by sending the documented
  probe to the running deployment and checking the documented status/body and
  failure criteria.
- The rollback requirement is verified by switching from the deployed
  revision to the retained previous revision after a failed verification (or
  an explicitly documented safe failure simulation), then rerunning the
  health probe against the restored deployment.
- The no-product-code-change constraint is verified with version-control
  inspection showing only the intended documentation/task changes.

### Additional implementation verification

- Check that secrets are absent from the runbook and acceptance transcript.
- Check that the instructions work with a clean dependency state rather than
  relying on ignored local caches or pre-existing processes.
- Check that rollback leaves a clearly identified previous release and that
  the runbook explains what happens to persistent book data, if the selected
  target has any.