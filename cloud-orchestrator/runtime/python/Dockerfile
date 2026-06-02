FROM public.ecr.aws/docker/library/ubuntu:22.04 AS runtime-base

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        git \
        openssh-client \
        python3 \
        python3-pip \
        python3-venv \
        rsync && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ai-agent-platform

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

RUN python3 -m pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    prompt_toolkit \
    python-dotenv \
    tomli \
    zeroconf \
    websockets \
    httpx \
    structlog \
    jsonpath-ng \
    trafilatura \
    GitPython \
    requests

FROM runtime-base AS plugin-bundler

COPY plugins ./plugins
COPY application/python/agent_terminal_app/default_config/config.json ./application/python/agent_terminal_app/default_config/config.json
COPY scripts/build_cloud_runtime_plugin_bundle.py ./scripts/build_cloud_runtime_plugin_bundle.py

RUN python3 scripts/build_cloud_runtime_plugin_bundle.py \
        --plugins-root plugins \
        --default-config application/python/agent_terminal_app/default_config/config.json \
        --output /tmp/cloud-runtime-plugin-bundle \
        --local-project-prefix ./plugins && \
    python3 -m pip wheel --wheel-dir /tmp/cloud-runtime-plugin-bundle/wheelhouse \
        -r /tmp/cloud-runtime-plugin-bundle/local-projects.txt

FROM runtime-base

COPY core/python/agent_core ./python_lib/agent_core
COPY core/python/agent_app ./python_lib/agent_app
COPY core/python/plugins ./python_lib/plugins
COPY core/python/sitecustomize.py ./python_lib/sitecustomize.py
COPY application/python/agent_terminal_app ./python_lib/agent_terminal_app
COPY cloud-orchestrator/runtime/python/runtime.py ./cloud-orchestrator/runtime/python/runtime.py
COPY --from=plugin-bundler /tmp/cloud-runtime-plugin-bundle ./cloud-runtime-plugin-bundle

RUN python3 -m pip install --no-cache-dir --no-index \
    --find-links=/opt/ai-agent-platform/cloud-runtime-plugin-bundle/wheelhouse \
    --no-deps \
    /opt/ai-agent-platform/cloud-runtime-plugin-bundle/wheelhouse/*.whl

ENV BUILTIN_PLUGINS=/opt/ai-agent-platform/cloud-runtime-plugin-bundle/bundled_plugins
ENV PYTHONPATH=/opt/ai-agent-platform/python_lib
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV LOG_POS=true
ENV CRYSTAL_SHELL_ERROR_CONTEXT=1
ENV CLOUD_AGENT_INSTANCE_DIR=/cloud-agent/instance
ENV CLOUD_AGENT_WORKSPACE_DIR=/cloud-agent/instance/workspace
ENV CLOUD_AGENT_SESSIONS_DIR=/cloud-agent/instance/sessions
ENV CLOUD_AGENT_CONFIG_PATH=/cloud-agent/instance/config/config.json
ENV CONFIG_DIR=/cloud-agent/instance/config/assets
ENV WORKING_DIR=/cloud-agent/instance/workspace
ENV CLOUD_WORKSPACE_DIR=/cloud-agent/instance/workspace
ENV TRANSFER_DIR=/transfer
ENV SESSION_DIR=/cloud-agent/instance/sessions

WORKDIR /opt/ai-agent-platform/cloud-orchestrator/runtime/python

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "runtime:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--access-log"]