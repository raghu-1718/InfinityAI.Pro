# Engine A - Orchestration & Risk Management

**Version**: v3.8-central-authority
**Status**: ✅ Production

## 🏛️ Central Authority
Engine A is the **sole autonomous authority** of the InfinityAI.Pro platform. It is responsible for:
1.  **Orchestration**: Managing the trading lifecycle.
2.  **Risk Gates**: Enforcing strict risk checks (VaR, Drawdown, Kelly).
3.  **Command**: Issuing explicit execution orders to Engine C.

## 🔄 Autonomous Loop (Internal)
Engine A runs an **internal asyncio-based scheduler** (`AutonomousTrader`) that:
- Triggers every 1-5 minutes.
- Fetches signals from Engine B.
- Validates them against Risk Gates.
- Commands Engine C to execute.

## 🛡️ Risk Management
Integrated risk module providing:
- **VaR / CVaR** (95% / 99%)
- **Kelly Criterion**
- **Sortino Ratio**
- **Maximum Drawdown**

## 🔗 Integrations
- **Google Gemini 2.5 Flash**: Strategy decision support.
- **DhanHQ via Engine C**: Indirect execution.
- **Engine B**: Signal ingestion.

## ⚠️ Constraints
- MUST NOT allow trades that fail Risk Gates.
- MUST NOT bypass Engine C for execution.
