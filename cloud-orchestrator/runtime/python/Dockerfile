FROM public.ecr.aws/docker/library/python:3.11-slim

RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /app
COPY runtime.py /app/runtime.py

ENV CLOUD_WORKSPACE_DIR=/workspace
ENV TRANSFER_DIR=/transfer
ENV SESSION_DIR=/sessions

EXPOSE 8000

CMD ["uvicorn", "runtime:app", "--host", "0.0.0.0", "--port", "8000"]