FROM public.ecr.aws/docker/library/python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential git rsync ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ai-agent-platform

COPY core/python ./core/python
COPY application/python ./application/python
COPY plugins ./plugins
COPY cloud-orchestrator/runtime/python/runtime.py ./cloud-orchestrator/runtime/python/runtime.py

RUN pip install --no-cache-dir \
    ./core/python \
    ./application/python \
    ./plugins/tool-compat-shared \
    ./plugins/web-fetch-shared

ENV BUILTIN_PLUGINS=/opt/ai-agent-platform/plugins
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

CMD ["uvicorn", "runtime:app", "--host", "0.0.0.0", "--port", "8000"]