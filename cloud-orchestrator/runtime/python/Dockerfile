FROM ubuntu:22.04

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

COPY core/python/agent_core ./python_lib/agent_core
COPY core/python/agent_app ./python_lib/agent_app
COPY core/python/plugins ./python_lib/plugins
COPY core/python/sitecustomize.py ./python_lib/sitecustomize.py
COPY application/python/agent_terminal_app ./python_lib/agent_terminal_app
COPY plugins ./plugins
COPY cloud-orchestrator/runtime/python/runtime.py ./cloud-orchestrator/runtime/python/runtime.py

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

ENV BUILTIN_PLUGINS=/opt/ai-agent-platform/plugins
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