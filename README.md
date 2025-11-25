# InfinityAI.Pro - AI-Powered Trading Platform

InfinityAI.Pro is an AI-driven trading platform designed for the Indian markets (NSE, BSE). It leverages a microservices architecture to provide real-time market data analysis, generate trading signals using machine learning, and execute trades securely.

## Architecture Overview

The platform is built on a robust and scalable microservices architecture, consisting of three core backend services, each containerized with Docker.

| Service             | Directory                | Description                                                                                              |
| ------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------- |
| **Engine Analytics**| `engine-analytics`       | The primary orchestrator. It fetches signals from `engine-core` and sends execution orders to `engine-execution`. |
| **Engine Core**     | `engine-core`            | The intelligence layer. It uses ML models to analyze market data and generate trading signals (BUY/SELL/HOLD).   |
| **Engine Execution**| `engine-execution`       | The execution layer. It securely places trades with the broker (DhanHQ) based on instructions from the analytics engine. |

All services are designed to be deployed independently on a cloud platform like Google Cloud Run.

## Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-analytics/     # Orchestrator and data aggregator
│   ├── engine-core/          # AI/ML signal generation
│   ├── engine-execution/     # Secure trade execution
│   ├── strategies/           # Trading strategy logic (e.g., momentum, mean-reversion)
│   └── docker-compose.yml    # Docker Compose for local development
├── frontend/
│   └── ...                   # (Future) React-based dashboard
└── README.md
```

## Getting Started

### Prerequisites

*   Docker and Docker Compose
*   Python 3.11+
*   An account with DhanHQ to get API credentials.

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/raghu-1718/InfinityAI.Pro.git
    cd InfinityAI.Pro
    ```

2.  **Set up Environment Variables:**

    Each service requires its own set of environment variables for configuration and secrets management. The primary method is to use a `.env` file in the root of the `backend` directory.

    Create a file named `.env` in the `backend/` directory and add the following, replacing placeholder values with your actual credentials:

    ```env
    # DhanHQ API Credentials
    DHAN_CLIENT_ID=your_dhan_client_id
    DHAN_ACCESS_TOKEN=your_dhan_access_token

    # Service URLs (for local communication)
    ENGINE_B_URL=http://engine-core:8000
    ENGINE_C_URL=http://engine-execution:8000

    # (Optional) Gemini API Key for advanced AI features
    GEMINI_API_KEY=your_gemini_api_key
    ```
    *Note: The `docker-compose.yml` file is configured to automatically load this `.env` file and pass the variables to the respective services.*

3.  **Run the entire backend stack:**

    Navigate to the `backend` directory and use Docker Compose to build and run all services:
    ```bash
    cd backend
    docker-compose up --build
    ```
    This command will start all three engines. You can monitor the logs in your terminal.

4.  **Verify the services:**

    Once the services are running, you can check their health status:
    *   **Engine Analytics:** `curl http://localhost:8001/healthz`
    *   **Engine Core:** `curl http://localhost:8002/healthz`
    *   **Engine Execution:** `curl http://localhost:8003/healthz`

    *(Note: Port mappings are `8001` for analytics, `8002` for core, and `8003` for execution)*

## API Endpoints

### Engine Analytics (`localhost:8001`)

*   `POST /orchestrate`: The main endpoint to trigger the trading workflow.
    *   **Body:** `{ "symbol": "RELIANCE", "qty": 1 }`
    *   This will fetch a signal from `engine-core` and, if the signal is not "HOLD", forward an order to `engine-execution`.

### Engine Core (`localhost:8002`)

*   `POST /api/predict`: Generates a trading signal.
    *   **Body:** `{ "symbol": "TCS" }`
    *   **Returns:** A signal like `{ "signal": "BUY", "confidence": 0.85, ... }`

### Engine Execution (`localhost:8003`)

*   `POST /api/dhan/place-order`: Places a trade order.
    *   **Body:** A detailed JSON payload specifying the order parameters (symbol, quantity, type, etc.). This is typically called by `engine-analytics`.

## Strategies

The `backend/strategies` directory holds the Python modules for different trading algorithms. The platform can be extended by adding new strategy files here. Current strategies include:
*   `mean_reversion.py`
*   `momentum.py`

## Security

*   **No Hardcoded Secrets:** All API keys, tokens, and sensitive configurations are managed through environment variables and are NOT hardcoded in the source.
*   **Containerization:** Docker provides a secure and isolated environment for each service.

## Next Steps

*   **Frontend:** Develop a React-based dashboard to visualize market data, signals, and trade history.
*   **Deployment:** Deploy the services to a cloud provider like Google Cloud Run or AWS ECS.
*   **CI/CD:** Implement a CI/CD pipeline using GitHub Actions to automate testing and deployment.
*   **Database:** Integrate a database like Firestore or PostgreSQL to persist trade history, user data, and signals.
