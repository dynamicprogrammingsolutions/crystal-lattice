# Dockerfile Container Profiles
Add container profile support for selecting a prebuilt image or building a
plugin/config-provided Dockerfile from a digest-addressed build context.

The cloud-agent plugin owns container profile resolution, the cloud runtime
Dockerfile/runtime assets, and the staged build context. The orchestrator owns
artifact storage, builder/registry wiring, and runner lifecycle operations.
Project workspace files must be mounted at runtime, not used as the Docker
build context. Project config may explicitly declare build assets such as
package manifests, lockfiles, or directories; those assets are copied into the
sanitized build context and included in the digest.

## Requirements checklist

- [x] Extend container profiles to support prebuilt image mode.
- [x] Extend container profiles to support Dockerfile build mode.
- [x] Make `mode` optional and infer it from profile shape: `dockerfile` present means Dockerfile mode, otherwise image mode.
- [x] Clean up profile resolution so documented/tested container profile fields are actually used by start and validation flows.
- [x] Move default cloud runtime Dockerfile/runtime ownership to the cloud-agent plugin, with no default Dockerfile/runtime on the cloud-orchestrator side.
- [x] Add digest-addressed build context artifact storage so the same context is transferred/stored once per digest, not once per instance.
- [x] Include project-declared build assets in the build context digest.
- [x] Allow declared build assets to be files or directories, with docs warning against volatile, large, generated, or secret-containing paths.
- [x] Keep runners responsible only for ensuring an image through deployment-wired builder/registry services and starting/stopping/proxying the runtime.
- [x] Keep package installation in Dockerfiles or install scripts, not hardcoded Elixir logic.
- [x] Add shared cached path mounts configured by container profile and shared between instances.
- [x] Add profile-defined runtime mounts for large mutable directories that should not live in Docker image layers.
- [x] Keep project workspace data mounted at runtime.
- [x] Ensure the orchestrator data directory is a durable mounted directory in Docker deployments.
- [x] Set up durable EBS-backed orchestrator data storage for the Ireland server.
- [x] Update the AWS stack to provision and mount EBS for the orchestrator data directory.
- [x] Preserve current default runtime image behavior.
- [x] Add unit tests for config parsing and Docker command construction.
- [ ] Add gated integration tests for Dockerfile build/run behavior if practical.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0120-cloud-profile-config-no-behavior-change.md`

## Current Behavior To Clean Up

Before this work, config supported `application.cloud_agent.container_profiles`,
but only `image` was used. `resolve_cloud_agent_profiles` selected
`default_container_profile`, stores `selected_container_profile`, and flattens
`container_profiles.<id>.image` into `runtime_image`. Start and validation flows
then used `runtime_image`; `selected_container_profile` was mostly
informational.

This task should make the resolved container profile the behavior source of
truth. Fields documented and asserted in tests must be consumed by the start and
validation paths, not only preserved in state.

## Profile Shape

Image mode example:

```json
{
  "mode": "image",
  "image": "cloud-agent-runtime:latest"
}
```

Dockerfile mode example:

```json
{
  "image": "cloud-agent-runtime-iocharts:latest",
  "dockerfile": "runtime/Dockerfile",
  "context": "runtime",
  "target": "cloud-agent",
  "build_args": {
    "PYTHON_VERSION": "3.12"
  },
  "build_assets": [
    {
      "source": "frontend/package.json",
      "target": "assets/frontend/package.json"
    },
    {
      "source": "frontend/yarn.lock",
      "target": "assets/frontend/yarn.lock"
    },
    {
      "source": "frontend/patches",
      "target": "assets/frontend/patches"
    }
  ],
  "cache_mounts": [
    {
      "id": "frontend-node-modules",
      "target": "/cloud-agent/instance/workspace/frontend/node_modules",
      "scope": "connection"
    }
  ],
  "mounts": [
    {
      "id": "ollama-models",
      "target": "/cloud-agent/cache/ollama",
      "scope": "profile"
    }
  ]
}
```

## Field Semantics

- `mode`: Optional. If present, use `image` or `dockerfile`. If omitted, infer
  `dockerfile` when `dockerfile` is present; otherwise infer `image`.
- `image`: Final runtime image reference. In Dockerfile mode, this is the image
  the builder produces and the runner starts.
- `dockerfile`: Dockerfile source path. Env placeholders are expanded; relative
  paths resolve relative to the current/project directory, like other config
  paths. The Dockerfile is copied into the staged context and sent to the
  builder as a staged relative path.
- `context`: Source directory to stage. Env placeholders are expanded; relative
  paths resolve relative to the current/project directory.
- `target`: Optional Docker build target. Included in the digest.
- `build_args`: Optional string build arguments. Included in the digest. Do not
  use for secrets.
- `build_assets`: Optional file or directory assets copied from the declaring
  project/config context into the staged build context. Included in the digest.
- `cache_mounts`: Named persistent runtime mounts for dependency caches or
  install outputs that should be shared between instances.
- `mounts`: Named persistent runtime mounts for large mutable data that should
  not be baked into Docker layers.

## Build Artifact Flow

1. The plugin resolves the selected container profile.
2. The plugin stages a sanitized build context containing the plugin-owned cloud
   runtime, Crystal Lattice runtime assets, Dockerfile, and declared build
   assets.
3. The plugin computes a digest over staged files plus build metadata.
4. The orchestrator stores the build context artifact by digest. A digest already
   present is reused.
5. The deployment-wired builder ensures the requested image exists for that
   digest.
6. The selected runner starts the runtime image with the standard runtime
   contract, workspace mount, transfer mount, cache mounts, and profile mounts.

For installed builds, precompute the default runtime build context digest during
packaging and store it in a manifest. If no project build assets modify the
default context, the plugin can use that manifest digest directly.

## Runner And Deployment Boundary

All deployment backends should consume the same resolved container/build
artifact contract. Docker, Kubernetes, and Fargate do not need separate
container profile mode declarations. The deployment must connect the
orchestrator to suitable builder and registry/image storage services:

- Docker deployment: local artifact store, local Docker builder, local Docker
  image store, Docker runner.
- Kubernetes/Fargate deployment: artifact storage plus external builder and
  registry, then Kubernetes/ECS runner starts the produced image.

## Persistence And Mounts

The orchestrator data directory must be durable because it stores transfers,
instances, runtime caches, build artifacts, and shared mount data. Docker
Compose deployments should mount this directory into the orchestrator container.
Remote deployments must provision durable storage for it.

Follow-up deployment work completed in this task:

- Ireland server: created and mounted 64 GiB gp3 EBS-backed storage for the
  orchestrator data directory.
- AWS stack: provisions, attaches, formats if needed, and mounts EBS for the
  orchestrator data directory before starting the orchestrator.

## Documentation Notes

Document that build assets are powerful but sharp:

- lockfiles and package manifests are ideal;
- directories are allowed;
- generated or frequently changing files cause rebuilds;
- large directories increase artifact storage and upload/build time;
- secrets must not be included in build assets or build args;
- project source should usually remain a runtime mount, not a build asset.

## Execution plan

Added during task completion.

1. Make `application.cloud_agent.container_profiles` resolve to a real
   `container` spec and make start/validation flows consume that spec instead
   of treating `selected_container_profile` as informational.
2. Add Dockerfile-mode context staging and digest calculation in the cloud-agent
   plugin. Include Dockerfile content, context contents, build args, target, and
   project-declared build assets in the digest.
3. Add orchestrator build-context artifact storage keyed by digest, with routes
   to check/register staged contexts so they can be transferred once and reused
   across instances.
4. Extend the Docker runner to consume the resolved `container` spec, ensure
   Dockerfile-mode images exist through local Docker build, reuse matching
   digest-labelled images, and run image-mode profiles directly.
5. Add profile-defined `cache_mounts` and `mounts` to the Docker runner using
   durable orchestrator data paths shared by configured scope.
6. Move active runtime image build paths toward plugin-owned runtime assets by
   preparing build contexts from `cloud-agent-app` assets.
7. Add focused unit tests for resolver behavior, staging/digest behavior,
   build-context storage, Docker command construction, and start/validation
   payload use.
8. Continue with plugin-provided default container profile injection, optional
   mode inference, path-origin cleanup, deletion/deprecation of orchestrator
   runtime defaults, and gated Docker integration coverage.
   The default-profile injection, inferred mode, path cleanup, and orchestrator
   runtime deletion were completed in this stage; gated Docker integration
   coverage remains open.

## Implementation notes

Added during task completion.

- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_profiles.py` now
  resolves container profile fields into `state["container"]`.
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_container.py` stages
  sanitized Docker build contexts and computes digests including declared build
  assets.
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py` sends
  `container` to `/instances`, stages/registers Dockerfile contexts with the
  orchestrator, and uses Dockerfile-mode staging for `validate-cloud`.
- `cloud-orchestrator/lib/cloud_orchestrator/build_context_store.ex` stores
  build contexts by digest from ready transfers.
- `cloud-orchestrator/lib/cloud_orchestrator/router.ex` exposes
  `GET /build-contexts/:digest` and `POST /build-contexts`.
- `cloud-orchestrator/lib/cloud_orchestrator/runner/docker.ex` consumes the
  resolved container spec, builds/reuses digest-labelled Dockerfile images, and
  mounts profile-defined shared data/cache paths.
- Active runtime build paths in remote Docker deploy, AWS CodeBuild, the
  frontend SDK local harness, and bundled-Python package construction now
  prepare a plugin-owned runtime context from `cloud-agent-app` assets.
- The cloud-agent plugin now injects the default Dockerfile container profile
  when app/project config omits container profile details.
- `mode` is inferred from profile shape when omitted.
- Dockerfile contexts and build asset sources are resolved with env placeholder
  expansion and absolute path storage before staging.
- `cloud-orchestrator/runtime/python/{Dockerfile,runtime.py}` were removed.

## Verification

Added during task completion.

- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
- `cd cloud-orchestrator && mix test`
- `PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_orchestrator_source_bundle.py application/python/tests/test_runtime_layout.py application/python/tests/test_python_runtime_package_builder.py -q`
- `python -m py_compile scripts/prepare_cloud_runtime_build_context.py scripts/build_crystal_lattice_binary.py scripts/build_crystal_lattice_python_runtime_package.py plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_validation.py`
- `bash -n cloud-orchestrator/deploy/remote-docker/deploy.sh cloud-orchestrator/deploy/lib/source_bundle.sh`
- `python -m json.tool application/python/agent_terminal_app/default_config.json >/dev/null && python -m json.tool application/python/agent_terminal_app/default_config/config.json >/dev/null && python -m json.tool application/python/agent_terminal_app/runtime_layout.json >/dev/null`
- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src python - <<'PY' ... AgentApplication('application/python/agent_terminal_app/default_config/config.json', ...) ...`
- `git diff --check`

## Stage Completion Notes

Added during task completion.

Completed the container-profile and durable data storage stage except for the
remaining gated Docker integration expansion. The cloud-agent plugin now
supplies the default Dockerfile container profile, so app default config no
longer needs to declare
`container_profiles`. Container profile `mode` is optional and inferred from
shape. Dockerfile/context/build asset source paths are expanded through env
placeholders and resolved to absolute paths before staging, while staged
Dockerfile and build asset targets remain safe relative paths inside the staged
context. The orchestrator-owned default runtime Dockerfile and runtime.py were
removed.

Remaining open item:

- Gated Docker integration coverage for tiny image mode, tiny Dockerfile mode,
  nested Dockerfile/context layouts, and the default plugin Dockerfile build.

## Regression Test Notes

Added during task completion.

After adding plugin-owned default Dockerfile profiles, the broader cloud E2E
suite exposed three test/deploy issues that were fixed in this stage:

- Cloud start actions can return an async operation before `connection_link`.
  The frontend SDK cloud orchestrator E2Es now poll the plugin-contributed
  `cloud.check_session_agent` action until the link is available.
- AWS E2E orchestrators are cached by the frontend harness. The cache now clears
  on AWS deploy teardown so later describes do not reuse a stopped deployment.
- The Codex default-config E2E expected `cloud.close_session` to copy workspace
  changes back. The real user workflow requires `cloud.sync_down` before close,
  so the test now uses that plugin action explicitly.
- AWS CodeBuild source-bundle runtime preparation failed on dangling symlinks
  in local plugin source trees. Sanitized tree copy now ignores dangling
  symlinks.

Regression commands completed successfully after those fixes:

- `npm run integration:cloud`
- `RUN_CLOUD_ORCHESTRATOR_E2E_BUILD_IMAGES=1 npm run integration:cloud`
- `npm run integration:cloud:profiles`
- `npm run integration:cloud:openrouter`
- `npm run integration:cloud:codex`
- `npm run integration:cloud:aws:fresh`
- `aws cloudformation validate-template --template-body file://cloud-orchestrator/deploy/aws-ec2/secure-origin.yaml --region us-east-1`
- `npm run integration:cloud:aws` with explicit prebuilt image URI env vars
  after adding the AWS EBS data-volume path.
- `.crystal/deploy-cloud-orchestrator-ireland.sh` after mounting the Ireland
  server data directory on EBS.
- `RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E=1 CLOUD_ORCHESTRATOR_REMOTE=irelandsrv@ireland-s1.dynamicprogrammingsolutions.com CLOUD_ORCHESTRATOR_PUBLIC_URL=https://crystal-lattice-cloud.dynamicprogrammingsolutions.com CLOUD_ORCHESTRATOR_HOST_DATA_DIR=/home/irelandsrv/cloud-orchestrator-data SSH_OPTS='-i ~/.ssh/srv-ireland.pem -o BatchMode=yes' npm run integration:cloud:remote-docker`
- `npm run integration:cloud:aws:codex` with explicit image URI env vars from
  the successful fresh build reached the EC2 default-config Codex provider flow;
  the `codex-openrouter` chain passed. The `codex-openai` case timed out waiting
  for startup/link and is treated as non-blocking for this stage because the
  OpenAI API key was known not to work during verification.

Commands not completed:

- Plain `npm run integration:cloud:aws:codex`: blocked because the non-fresh AWS
  harness path creates a new stack and requires prebuilt image URI metadata for
  that same stack. It can be run by providing `CLOUD_ORCHESTRATOR_IMAGE_URI`,
  `CLOUD_AGENT_RUNTIME_IMAGE_URI`, and `CLOUD_AGENT_TRANSFER_SSH_IMAGE_URI`.

Ireland EBS deployment notes:

- EC2 instance: `i-0d675c4913029c747` in `eu-west-1c`.
- New volume: `vol-08d736561dbdda564`, 64 GiB gp3 encrypted EBS.
- Mounted at `/home/irelandsrv/cloud-orchestrator-data` as ext4 via `/etc/fstab`.
- Root disk went from about 94% used before migration to about 54% used after
  migration and redeploy.
- Public health check after migration/redeploy:
  `https://crystal-lattice-cloud.dynamicprogrammingsolutions.com/health`.
- The remote Docker smoke left two runtime containers running; they were removed
  after the passing test. The health endpoint remained healthy but still reported
  stale registry counts (`instances: 2`, `transfers: 3`) after container cleanup.
