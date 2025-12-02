# =====================================================================
# InfinityAI.Pro - Engine A (Orchestration & Risk Management)
# ML: Scikit-learn, NumPy, Pandas, CVXPY (Portfolio Optimization)
# =====================================================================
FROM python:3.11-slim

# Install build dependencies for CVXPY
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./src /app/src

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
