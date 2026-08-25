# InfinityAI.Pro - System Architecture & Technical Documentation

**Version:** 4.1
**Last Updated:** 2026-08-16

This document provides a comprehensive overview of the InfinityAI.Pro system architecture, from the cloud infrastructure to the application code and data flows. It is intended to be the single source of truth for the project's technical design.

## 1. High-Level Architecture

InfinityAI.Pro is a multi-service algorithmic trading platform built on Google Cloud Platform (GCP) and Firebase. It is designed as a microservices-style architecture to separate concerns and allow for independent scaling of components.

The core components are:
- **Frontend Web App**: A Next.js application for user interaction, portfolio visualization, and signal display.
- **Engine B (AI/ML Core)**: The primary backend service responsible for data processing, ML model inference, and AI-powered signal generation.
- **Engine C (Broker Gateway)**: A service that acts as a secure proxy and wrapper for the DhanHQ trading API.
- **Engine A (Auxiliary Service)**: A lightweight service, currently serving as a placeholder or for minor tasks.
- **GCP Services**: A suite of managed services for data storage, AI/ML, and hosting.
- **Firebase**: Provides hosting for the frontend and a NoSQL database (Firestore) for application data.

**Note**: An architecture diagram would visually represent this flow.

**Logical Flow:**
1.  A user interacts with the **Frontend Web App** (hosted on Firebase).
2.  For AI signals or analysis, the frontend calls **Engine B**.
3.  **Engine B** fetches market data from **BigQuery** or live from **Engine C**.
4.  **Engine B** processes the data, runs it through its local ML model ensemble, and queries **Vertex AI (Gemini)** for advanced analysis.
5.  The generated signal is stored in **Firestore** and returned to the user via the frontend.
6.  **Engine C** communicates with the **DhanHQ API** for live market data, order execution, and account management.
7.  ML models are stored in **Cloud Storage** and are hot-reloaded by Engine B.

---

## 2. Component Deep-Dive

### 2.1. Frontend (`frontend/web-app`)
- **Framework**: React with Next.js
- **Language**: TypeScript (`.tsx`)
- **UI Components**: Shadcn UI (`components/ui`)
- **Deployment**: Firebase Hosting
- **Key Features**:
    - User authentication and portfolio management.
    - Real-time display of AI-generated trading signals.
    - Interactive charts and data tables.
    - Communicates with Engine B's REST API endpoints.

### 2.2. Engine B (`backend/engine-b`) - AI/ML Core
This is the most critical component of the system.
- **Framework**: FastAPI (Python)
- **Deployment**: Google Compute Engine (GCE) VM at `http://35.200.135.175:8080`. This allows for direct GPU access if needed.
- **Key Responsibilities**:
    - **Signal Generation**: Exposes `/api/v1/signal` and other endpoints to generate trading signals using a hybrid approach of rule-based analysis, a local ML ensemble, and GenAI.
    - **ML Model Ensemble**: Manages a weighted ensemble of models (XGBoost, LightGBM, CatBoost, RandomForest) for robust predictions. See `MLModelStore` class.
    - **Deep Learning**: Integrates LSTM for price forecasting and potentially DQN for reinforcement learning-based actions.
    - **Data Processing**: The `MarketDataEngine` class fetches and processes historical and live market data, with a fallback mechanism (DhanHQ -> Yahoo Finance -> Synthetic).
    - **GenAI Integration**: Leverages `EnhancedGenAIClient` to interact with Vertex AI Gemini models for complex analysis, options strategies, and market summaries.
    - **API Routing**: Includes various API routes, such as `/analyze-options` for on-demand analysis.

### 2.3. Engine C (`backend/engine-c`) - Broker Gateway
- **Framework**: FastAPI (Python)
- **Deployment**: Google Cloud Run (serverless, auto-scaling).
- **Key Responsibilities**:
    - Acts as a secure wrapper around the DhanHQ trading API.
    - Manages user credentials and API keys securely.
    - Provides a consistent internal API for fetching funds, placing orders, and getting live data, abstracting away the direct broker interaction from Engine B.
    - Handles rate limiting and error mitigation for the external broker API.

### 2.4. Engine A (`backend/engine-a`) - Auxiliary Service
- **Framework**: FastAPI (Python)
- **Deployment**: Google Cloud Run.
- **Key Responsibilities**:
    - Currently serves a basic health check.
    - Can be used for lightweight, non-critical tasks like logging or simple webhooks.

---

## 3. GCP & Firebase Infrastructure

The infrastructure is managed via Terraform (`infra/gcp`). The GCP Project ID is **`project-841b7f97-5ee3-4fbe-920`**.

### 3.1. Google Cloud Platform (GCP)
- **Compute Engine (GCE)**: A VM hosts Engine B to ensure consistent performance and potential GPU attachment for ML model training/inference.
- **Cloud Run**: Hosts the serverless, containerized Engine A and Engine C, providing auto-scaling and cost-efficiency.
- **Vertex AI**: The core of the GenAI capabilities.
    - **Models Used**: `gemini-2.5-pro` (for deep analysis) and `gemini-2.5-flash` (for fast, cost-effective queries).
    - **Location**: `asia-south1`.
    - **Usage**: Powers endpoints like `/analyze-options` and provides natural language trading insights.
- **BigQuery**: The data warehouse for the platform.
    - **Dataset**: `market_data`.
    - **Table**: `options_ticks` stores historical options data.
    - **Usage**: Used by Engine B for fetching bulk historical data for analysis.
- **Cloud Storage**:
    - **Bucket**: `infinity-ai-models-vault`.
    - **Usage**: Persists trained ML models (e.g., `.pkl`, `.cbm` files) for hot-reloading by Engine B.
- **Cloud Run Service Discovery**: The `audit_system_health.py` script uses the `google-cloud-run` SDK to dynamically find the live URLs of Engine A and C in the `asia-south1` region.

### 3.2. Firebase
- **Firestore**: A NoSQL, document-based database.
    - **Usage**:
        - Storing user credentials and profiles.
        - Persisting generated AI signals for historical review and user display.
        - Used by the health audit script for a dummy read/write test.
- **Firebase Hosting**:
    - **Usage**: Hosts the static and server-side rendered assets of the Next.js frontend application, providing a global CDN for fast delivery.

---

## 4. Code & Technical Verification

### 4.1. Key Code Modules
- **`backend/engine-b/src/main.py`**: The entry point and main application file for the core AI engine. It orchestrates all components: models, data engines, risk managers, and API endpoints.
- **`backend/engine-b/src/api/routes/market_analysis.py`**: An example of a feature-specific API route. It queries BigQuery, formats a prompt, and calls Vertex AI to get trading insights.
- **`backend/shared/`**: A critical directory containing shared Python modules used across different backend services.
    - `google_integrations/`: Contains clients for GenAI, Cloud Storage, etc.
    - `performance/`: Caching and connection pooling utilities.
    - `structured_logging.py`: For consistent, machine-readable logs.
- **`tools/verification/`**: A collection of Python scripts used for manual testing and verification of different parts of the system (e.g., `check_firestore.py`, `verify_dhan_connection.py`).

### 4.2. System Health Audit (`audit_system_health.py`)
This is the primary diagnostic script for ensuring the end-to-end health of the entire platform.
- **Location**: Project root.
- **Execution**: `python audit_system_health.py`
- **Functionality**:
    - Asynchronously tests all major service integrations.
    - **Firebase/Firestore**: Performs a test write, read, and delete in a dummy collection.
    - **BigQuery**: Runs a `COUNT(*)` query on the `options_ticks` table to verify permissions and connectivity.
    - **Vertex AI**: Sends a "Ping" prompt to the configured Gemini model to verify API access and inference.
    - **Cloud Storage**: Checks for the existence of the `infinity-ai-models-vault` bucket.
    - **Engine Health**: Pings the `/health` endpoints of the deployed Engine A, B, and C services, using auto-discovered URLs for the Cloud Run services.
- **Output**: Provides a color-coded terminal report summarizing the status (OK/FAILED), latency, and detailed error messages for each service, along with a list of required fixes.

---

## 5. Data Flow Example: Options Analysis Request

1.  **User Action**: User requests an analysis for "NIFTY" options via the frontend.
2.  **API Call**: The frontend makes a `POST` request to Engine B's `/analyze-options` endpoint with `{"ticker": "NIFTY"}`.
3.  **Data Fetching (Engine B)**:
    - The `analyze_options_data` function in `market_analysis.py` is triggered.
    - It connects to BigQuery using the `google-cloud-bigquery` client.
    - It executes a SQL query: `SELECT * FROM \`project-841b7f97-5ee3-4fbe-920.market_data.options_ticks\` WHERE underlying = 'NIFTY' ORDER BY timestamp DESC LIMIT 5`.
4.  **Prompt Engineering (Engine B)**:
    - The 5 rows returned from BigQuery are formatted into a human-readable string.
    - This string is injected into a larger prompt template that asks Gemini for institutional-grade insights on OI and IV.
5.  **GenAI Inference (Engine B -> Vertex AI)**:
    - Engine B's `EnhancedGenAIClient` sends the final prompt to the Vertex AI endpoint.
    - Vertex AI routes the request to the `gemini-2.5-pro` model.
6.  **Response Handling (Engine B)**:
    - The AI's text response is received.
    - Engine B packages this response into a JSON object: `{"analysis": "..."}`.
7.  **Return to User**: The JSON response is sent back to the frontend and displayed to the user.
