# Engine B - Delegating Dockerfile to existing implementation
FROM python:3.11-slim
WORKDIR /app

COPY backend/engines/engine-b/ /app/backend/engines/engine-b/
COPY backend/engine-b/main.py /app/backend/engine-b/main.py
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/engines/engine-b/requirements.txt \
    && pip install --no-cache-dir -r /app/backend/requirements.txt || true

ENV PORT=8001
EXPOSE 8001

CMD ["python", "-m", "uvicorn", "backend.engine-b.main:app", "--host", "0.0.0.0", "--port", "8001"]
