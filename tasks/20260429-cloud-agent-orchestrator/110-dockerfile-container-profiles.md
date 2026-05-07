# Dockerfile Container Profiles
Add container profile support for selecting a prebuilt image or building a repository/config-provided Dockerfile.

## Requirements checklist

- [ ] Extend container profiles to support prebuilt image mode.
- [ ] Extend container profiles to support Dockerfile build mode.
- [ ] Keep Docker runner responsible only for building/starting/stopping the selected container type.
- [ ] Keep package installation in Dockerfiles or install scripts, not hardcoded Elixir logic.
- [ ] Preserve current default runtime image behavior.
- [ ] Add unit tests for config parsing and Docker command construction.
- [ ] Add gated integration tests for Dockerfile build/run behavior if practical.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/070-cloud-profile-config-no-behavior-change.md`

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
  "mode": "dockerfile",
  "dockerfile": ".cloud-agent/container/Dockerfile",
  "context": ".",
  "target": "cloud-agent",
  "build_args": {
    "PYTHON_VERSION": "3.12"
  }
}
```

The Docker runner can build a project-specific image and then run it with the same runtime contract.
