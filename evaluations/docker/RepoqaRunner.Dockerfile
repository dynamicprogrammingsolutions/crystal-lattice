FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/ai-agent-platform

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY repo-source.tar.gz /tmp/repo-source.tar.gz
COPY agent_evaluations-*.whl /tmp/

RUN mkdir -p /opt/ai-agent-platform \
    && tar -xzf /tmp/repo-source.tar.gz -C /opt/ai-agent-platform \
    && rm /tmp/repo-source.tar.gz

RUN pip install -e /opt/ai-agent-platform/core/python \
    -e /opt/ai-agent-platform/application/python \
    /tmp/agent_evaluations-*.whl \
    && rm /tmp/agent_evaluations-*.whl

ENV BUILTIN_PLUGINS=/opt/ai-agent-platform/plugins

CMD ["python", "-m", "agent_evaluations", "--help"]