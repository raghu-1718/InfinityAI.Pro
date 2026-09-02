import pytest
from datetime import datetime

def test_health_endpoint(client):
    """Verify system health and metadata response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "market_status" in data

def test_market_tick_ingestion_success(client):
    """Verify valid tick ingestion returns 201 and echoes correlation ID."""
    corr_id = "corr-tick-001"
    payload = {
        "symbol": "NIFTY",
        "price": 24530.25,
        "volume": 2500,
        "strike_price": 24500,
        "option_type": "CE",
        "open_interest": 820000,
        "timestamp": datetime.utcnow().isoformat()
    }
    response = client.post(
        "/api/v1/market/ticks",
        json=payload,
        headers={"x-correlation-id": corr_id}
    )
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["status"] == "ingested"
    assert "tick_id" in res_data
    assert response.headers.get("x-correlation-id") == corr_id

def test_market_tick_ingestion_validation_error(client):
    """Invalid tick data must return 422 Unprocessable Entity."""
    payload = {
        "symbol": "NIFTY",
        "price": -100.0,  # Negative price
        "volume": -5
    }
    response = client.post("/api/v1/market/ticks", json=payload)
    assert response.status_code == 422

def test_get_market_ticks(client):
    """Verify retrieval of recent market ticks filtered by symbol."""
    # First ingest a test tick
    client.post(
        "/api/v1/market/ticks",
        json={
            "symbol": "BANKNIFTY",
            "price": 51500.0,
            "volume": 1200,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    response = client.get("/api/v1/market/ticks?symbol=BANKNIFTY&limit=5")
    assert response.status_code == 200
    ticks = response.json()
    assert isinstance(ticks, list)
    assert len(ticks) >= 1
    assert ticks[0]["symbol"] == "BANKNIFTY"

def test_model_inference_ensemble(client):
    """Verify Tri-Model ensemble inference returns predictions and consensus."""
    corr_id = "corr-inf-001"
    payload = {
        "features": {
            "close": 24500.0,
            "rsi_14": 58.2,
            "macd": 14.5,
            "volatility_20": 0.15,
            "oi_pcr": 1.15
        },
        "models": ["catboost", "lightgbm", "xgboost"]
    }
    response = client.post(
        "/api/v1/models/inference",
        json=payload,
        headers={"x-correlation-id": corr_id}
    )
    assert response.status_code == 200
    res = response.json()
    assert "predictions" in res
    assert "catboost" in res["predictions"]
    assert "lightgbm" in res["predictions"]
    assert "xgboost" in res["predictions"]
    assert "consensus_signal" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0

def test_models_status(client):
    """Verify model registry status endpoint."""
    response = client.get("/api/v1/models/status")
    assert response.status_code == 200
    status = response.json()
    assert "models" in status
    assert "ensemble_strategy" in status

def test_backtest_run_and_retrieval(client):
    """Verify triggering a backtest run and querying results."""
    payload = {
        "strategy": "tri_model_ensemble",
        "symbol": "NIFTY",
        "start_date": "2025-01-01",
        "end_date": "2025-06-30",
        "initial_capital": 200000.0,
        "slippage_pct": 0.0005,
        "include_sebi_taxes": True
    }
    run_resp = client.post("/api/v1/backtest/run", json=payload)
    assert run_resp.status_code == 202
    data = run_resp.json()
    assert "run_id" in data
    run_id = data["run_id"]
    assert data["status"] in ["completed", "running"]

    # Query backtest result by run_id
    get_resp = client.get(f"/api/v1/backtest/{run_id}")
    assert get_resp.status_code == 200
    result = get_resp.json()
    assert result["run_id"] == run_id
    assert "metrics" in result
    assert "sharpe_ratio" in result["metrics"]
    assert "max_drawdown" in result["metrics"]

def test_portfolio_state(client):
    """Verify portfolio state endpoint returns equity, margin, and VaR."""
    response = client.get("/api/v1/portfolio/state")
    assert response.status_code == 200
    state = response.json()
    assert "total_equity" in state
    assert "cash_balance" in state
    assert "dynamic_var_99" in state
    assert "positions" in state

def test_market_hours_enforcement_block_live(client):
    """Live trading outside market hours must return HTTP 403 Forbidden."""
    payload = {
        "symbol": "NIFTY",
        "action": "BUY",
        "quantity": 50,
        "price": 24500.0,
        "correlation_id": "corr-order-001"
    }
    # Simulate non-market hours live execution
    response = client.post(
        "/api/v1/portfolio/order",
        json=payload,
        headers={"x-force-market-closed": "true", "x-trading-mode": "live"}
    )
    assert response.status_code == 403
    err = response.json()
    assert "Market closed" in err["detail"]
