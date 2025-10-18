# Engine A - Delegating Dockerfile to existing implementation
FROM python:3.11-slim
WORKDIR /app

# Copy only engine-a implementation and root requirements
COPY backend/engines/engine-a/ /app/backend/engines/engine-a/
COPY backend/engine-a/main.py /app/backend/engine-a/main.py
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/engines/engine-a/requirements.txt \
    && pip install --no-cache-dir -r /app/backend/requirements.txt || true

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "backend.engine-a.main:app", "--host", "0.0.0.0", "--port", "8080"]
