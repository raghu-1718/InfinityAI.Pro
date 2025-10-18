# Engine C - Delegating Dockerfile to existing implementation
FROM python:3.11-slim
WORKDIR /app

COPY backend/engines/engine-c-execution/ /app/backend/engines/engine-c-execution/
COPY backend/engine-c/main.py /app/backend/engine-c/main.py
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/engines/engine-c-execution/requirements.txt \
    && pip install --no-cache-dir -r /app/backend/requirements.txt || true

ENV PORT=8002
EXPOSE 8002

CMD ["python", "-m", "uvicorn", "backend.engine-c.main:app", "--host", "0.0.0.0", "--port", "8002"]
