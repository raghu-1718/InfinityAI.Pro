# Engine C Elite Service

Self-learning, real-time, auto-hedging trading intelligence integrated with DhanHQ v2 APIs.

- REST + WebSocket (multi-channel)
- AI signal validation + auto-hedging
- Live portfolio reconciliation with PnL tracking
- Async-friendly and scalable on Cloud Run

## 🏗 Architecture (Pure Execution Worker)

Engine C is a **strictly passive execution system**. It:
1.  Receives explicit order commands from **Engine A**.
2.  Optimizes execution (slippage, timing).
3.  Routes orders to DhanHQ.
4.  Returns execution metrics.

**IT DOES NOT:**
- Initiate trades autonomously.
- Run background loops.
- Make risk decisions.

This package is intended to be embedded and started by Engine C FastAPI app via background runner.
