FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential gcc g++ git \
	liblapack-dev libblas-dev libgomp1 \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create engines dir and copy shared security middleware + __init__.py
RUN mkdir -p engines
COPY engines/security_middleware.py engines/
COPY engines/__init__.py engines/

# Copy engine-b specific files
COPY engines/engine-b/ .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]