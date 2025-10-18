# Engine D - Delegating Dockerfile to existing implementation
FROM python:3.11-slim
WORKDIR /app

COPY backend/engines/engine-d/ /app/backend/engines/engine-d/
COPY backend/engine-d/main.py /app/backend/engine-d/main.py
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/engines/engine-d/requirements.txt \
    && pip install --no-cache-dir -r /app/backend/requirements.txt || true

ENV PORT=8003
EXPOSE 8003

CMD ["python", "-m", "uvicorn", "backend.engine-d.main:app", "--host", "0.0.0.0", "--port", "8003"]
