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
        python3-dev \
        python3-pip \
        python3-venv \
        ripgrep \
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

COPY plugin_sources ./plugin_sources
COPY cloud-runtime-plugin-bundle ./cloud-runtime-plugin-bundle

RUN mkdir -p /tmp/cloud-runtime-plugin-bundle && \
    cp -a cloud-runtime-plugin-bundle/bundled_plugins /tmp/cloud-runtime-plugin-bundle/bundled_plugins && \
    cp cloud-runtime-plugin-bundle/manifest.json /tmp/cloud-runtime-plugin-bundle/manifest.json && \
    cp cloud-runtime-plugin-bundle/local-projects.txt /tmp/cloud-runtime-plugin-bundle/local-projects.txt && \
    python3 -m pip wheel --wheel-dir /tmp/cloud-runtime-plugin-bundle/wheelhouse \
        -r cloud-runtime-plugin-bundle/local-projects.txt

FROM runtime-base

COPY python_lib ./python_lib
COPY runtime.py ./cloud-orchestrator/runtime/python/runtime.py
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