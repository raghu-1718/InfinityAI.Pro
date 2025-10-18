from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import os
from core.logger import logger
from core.security_middleware import add_security_headers
from core.utils import load_config
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import io
import csv
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = FastAPI(
    title="InfinityAI Engine A - Modular",
    description="Market Data, Option Chain, AI, Dhan Integration",
    version="7.0.0"
)

# CORS and Security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_security_headers(app)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-a",
        "version": "7.0.0",
        "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
    }

# Version endpoint
@app.get("/version")
async def version_info():
    """Version and build information for deployment tracking"""
    from datetime import datetime
    return {
        "service": "engine-a-market-data",
        "version": "7.0.0",
        "build_date": "2025-10-18",
        "commit_sha": os.getenv("GIT_COMMIT", "local"),
        "features": ["market-data", "dhan-integration", "technical-analysis", "ai-signals"],
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "InfinityAI Engine A",
        "version": "7.0.0",
        "status": "operational",
        "description": "Modular Engine A for market data, analytics, and AI endpoints"
    }

# Import provider modules (real implementations) - wrapped in try/except for graceful degradation
try:
    from providers.dhan import DhanProvider
    dhan = DhanProvider()
    logger.info("DhanProvider loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load DhanProvider: {e}")
    dhan = None

try:
    from providers.gemini import GeminiProvider
    gemini = GeminiProvider()
    logger.info("GeminiProvider loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load GeminiProvider: {e}")
    gemini = None

try:
    from providers.huggingface import HuggingFaceProvider
    huggingface = HuggingFaceProvider()
    logger.info("HuggingFaceProvider loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load HuggingFaceProvider: {e}")
    huggingface = None

try:
    from analytics.ta import TechnicalAnalytics
    analytics = TechnicalAnalytics()
    logger.info("TechnicalAnalytics loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load TechnicalAnalytics: {e}")
    analytics = None

# Market signals (real)
@app.get("/api/signals")
async def get_market_signals():
    if analytics is None:
        raise HTTPException(status_code=503, detail="TechnicalAnalytics not available")
    try:
        signals = await analytics.get_signals()
        return {
            "status": "success",
            "signals": signals,
            "count": len(signals),
            "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
        }
    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market data endpoint (NEW)
@app.get("/api/marketdata")
async def get_market_data():
    """
    Returns live or sample market data for frontend integration.
    """
    if analytics is not None and hasattr(analytics, "get_market_data"):
        try:
            data = await analytics.get_market_data()
            return {
                "status": "success",
                "market_data": data,
                "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
            }
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    # Fallback: return sample data
    return {
        "status": "success",
        "market_data": [
            {"symbol": "NIFTY", "price": 22450.25, "change": 0.45, "volume": 1200000},
            {"symbol": "BANKNIFTY", "price": 48200.10, "change": -0.12, "volume": 800000},
            {"symbol": "RELIANCE", "price": 2850.75, "change": 1.02, "volume": 500000},
            {"symbol": "TCS", "price": 3950.00, "change": 0.88, "volume": 300000}
        ],
        "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
    }

# Dhan positions (real)
@app.get("/api/dhan/positions")
async def get_dhan_positions():
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        positions = await dhan.get_positions()
        return positions
    except Exception as e:
        logger.error(f"Failed to get Dhan positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dhan orders (real)
@app.get("/api/dhan/orders")
async def get_dhan_orders():
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        orders = await dhan.get_orders()
        return orders
    except Exception as e:
        logger.error(f"Failed to get Dhan orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dhan option chain (real)
@app.get("/api/dhan/optionchain/{symbol}")
async def get_dhan_option_chain(symbol: str):
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        option_chain = await dhan.get_option_chain(symbol)
        return {"symbol": symbol, "data": option_chain}
    except Exception as e:
        logger.error(f"Failed to get Dhan option chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dhan callback (real)
@app.get("/api/dhan/callback")
async def dhan_callback(code: str = None):
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    logger.info(f"Dhan callback received with code: {code}")
    # Real callback logic (e.g., OAuth, token exchange)
    result = await dhan.handle_callback(code)
    return result

# Dhan account statement (orders mapped as statements) with filters and pagination
@app.get("/api/dhan/statement")
async def dhan_statement(
    page: int = 1,
    page_size: int = 25,
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    status: Optional[str] = None,
    frm: Optional[str] = None,
    to: Optional[str] = None,
):
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        stmt = await dhan.get_statement()
        rows: List[Dict[str, Any]] = stmt.get("rows", []) if isinstance(stmt, dict) else []
        # Normalize rows for filtering
        def norm_row(r: Dict[str, Any]):
            return {
                "orderId": r.get("orderId") or r.get("id"),
                "symbol": (r.get("symbol") or r.get("tradingSymbol") or "").upper(),
                "side": (r.get("side") or r.get("transactionType") or "").upper(),
                "qty": r.get("qty") or r.get("quantity"),
                "price": r.get("price") or r.get("avgPrice"),
                "status": (r.get("status") or r.get("orderStatus") or "").upper(),
                "time": r.get("time") or r.get("orderTime") or r.get("timestamp"),
            }
        norm_rows = [norm_row(r) for r in rows]
        # Filtering
        if symbol:
            s = symbol.upper()
            norm_rows = [r for r in norm_rows if s in (r.get("symbol") or "").upper()]
        if side:
            sd = side.upper()
            norm_rows = [r for r in norm_rows if (r.get("side") or "").upper() == sd]
        if status:
            st = status.upper()
            norm_rows = [r for r in norm_rows if (r.get("status") or "").upper() == st]
        def parse_dt(v: Optional[str]) -> Optional[datetime]:
            if not v:
                return None
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return None
        start_dt = parse_dt(frm)
        end_dt = parse_dt(to)
        if start_dt or end_dt:
            def row_dt(r):
                return parse_dt(r.get("time"))
            filtered = []
            for r in norm_rows:
                t = row_dt(r)
                if t is None:
                    continue
                if start_dt and t < start_dt:
                    continue
                if end_dt and t > end_dt:
                    continue
                filtered.append(r)
            norm_rows = filtered
        # Pagination
        total = len(norm_rows)
        page = max(page, 1)
        page_size = max(min(page_size, 200), 1)
        start = (page - 1) * page_size
        end = start + page_size
        items = norm_rows[start:end]
        return {
            "source": stmt.get("source", "orders"),
            "rows": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }
    except Exception as e:
        logger.error(f"Failed to get Dhan statement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CSV export
@app.get("/api/dhan/statement.csv")
async def export_statement_csv():
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        stmt = await dhan.get_statement()
        rows: List[Dict[str, Any]] = stmt.get("rows", []) if isinstance(stmt, dict) else []
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["time", "orderId", "symbol", "side", "qty", "price", "status"])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "time": r.get("time") or r.get("orderTime") or r.get("timestamp"),
                "orderId": r.get("orderId") or r.get("id"),
                "symbol": r.get("symbol") or r.get("tradingSymbol"),
                "side": r.get("side") or r.get("transactionType"),
                "qty": r.get("qty") or r.get("quantity"),
                "price": r.get("price") or r.get("avgPrice"),
                "status": r.get("status") or r.get("orderStatus"),
            })
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(content=csv_bytes, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=statement.csv"})
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# PDF export
@app.get("/api/dhan/statement.pdf")
async def export_statement_pdf():
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        stmt = await dhan.get_statement()
        rows: List[Dict[str, Any]] = stmt.get("rows", []) if isinstance(stmt, dict) else []
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        width, height = letter
        y = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "InfinityAI.Pro - Trading Statement")
        y -= 20
        c.setFont("Helvetica", 9)
        headers = ["Time", "Order ID", "Symbol", "Side", "Qty", "Price", "Status"]
        c.drawString(50, y, " | ".join(headers))
        y -= 15
        for r in rows[:1000]:
            line = [
                str(r.get("time") or r.get("orderTime") or r.get("timestamp") or "-"),
                str(r.get("orderId") or r.get("id") or "-"),
                str(r.get("symbol") or r.get("tradingSymbol") or "-"),
                str(r.get("side") or r.get("transactionType") or "-"),
                str(r.get("qty") or r.get("quantity") or "-"),
                str(r.get("price") or r.get("avgPrice") or "-"),
                str(r.get("status") or r.get("orderStatus") or "-"),
            ]
            c.drawString(50, y, " | ".join(line))
            y -= 12
            if y < 50:
                c.showPage()
                y = height - 50
        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=statement.pdf"})
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New: Dhan overview aggregator (funds, holdings, positions, orders, profile)
@app.get("/api/dhan/overview")
async def dhan_overview():
    if dhan is None:
        raise HTTPException(status_code=503, detail="DhanProvider not available")
    try:
        funds, holdings, positions, orders, profile = await asyncio.gather(
            dhan.get_fundlimit(),
            dhan.get_holdings(),
            dhan.get_positions(),
            dhan.get_orders(),
            dhan.get_profile()
        )
        # Normalize holdings/positions minimal fields for UI
        def _norm_pos(p: Dict[str, Any]):
            qty = p.get("quantity") or p.get("netQty") or 0
            avg = p.get("avgPrice") or p.get("buyAvg") or 0.0
            ltp = p.get("ltp") or p.get("lastTradedPrice") or 0.0
            invested = qty * avg
            current = qty * ltp
            pnl = (current - invested)
            pct = (pnl / invested * 100.0) if invested > 0 else 0.0
            return {
                "symbol": p.get("tradingSymbol") or p.get("symbol") or "?",
                "qty": qty,
                "avg_price": avg,
                "ltp": ltp,
                "invested": invested,
                "current_value": current,
                "pnl": pnl,
                "pnl_pct": pct,
                "side": p.get("positionType") or p.get("productType") or "INTRADAY"
            }
        norm_positions = [_norm_pos(p) for p in (positions if isinstance(positions, list) else [])]

        def _norm_hold(h: Dict[str, Any]):
            qty = h.get("quantity") or h.get("qty") or 0
            avg = h.get("averagePrice") or h.get("avgPrice") or 0.0
            ltp = h.get("ltp") or h.get("lastTradedPrice") or 0.0
            invested = qty * avg
            current = qty * (ltp or avg)
            pnl = current - invested
            pct = (pnl / invested * 100.0) if invested > 0 else 0.0
            return {
                "symbol": h.get("tradingSymbol") or h.get("symbol") or "?",
                "qty": qty,
                "avg_price": avg,
                "ltp": ltp,
                "invested": invested,
                "current_value": current,
                "pnl": pnl,
                "pnl_pct": pct
            }
        norm_holdings = [_norm_hold(h) for h in (holdings if isinstance(holdings, list) else [])]

        return {
            "status": "success",
            "funds": funds,
            "profile": profile,
            "positions": norm_positions,
            "holdings": norm_holdings,
            "orders": orders,
            "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
        }
    except Exception as e:
        logger.error(f"Dhan overview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New: Exchanges catalog for India (static list for now)
@app.get("/api/exchanges")
async def list_exchanges():
    return {
        "status": "success",
        "exchanges": [
            {"code": "NSE", "name": "National Stock Exchange of India", "segments": ["NSE_EQ", "NSE_FO", "NSE_CDS"]},
            {"code": "BSE", "name": "BSE (Bombay Stock Exchange)", "segments": ["BSE_EQ", "BSE_FO"]},
            {"code": "MCX", "name": "Multi Commodity Exchange", "segments": ["MCX_FUT", "MCX_OPT"]},
            {"code": "NSEIX", "name": "NSE Indices (Benchmarks)", "segments": ["INDEX"]}
        ],
        "timestamp": os.getenv("CURRENT_TIMESTAMP", "2025-10-17 UTC")
    }

# New: AI Option Chain best analysis for index (delegates to analytics if available)
@app.get("/api/optionchain/ai/{index_symbol}")
async def optionchain_ai(index_symbol: str):
    try:
        # If TechnicalAnalytics has option chain analysis, use it
        if analytics is not None and hasattr(analytics, "best_option_chain_analysis"):
            result = await analytics.best_option_chain_analysis(index_symbol.upper())
            return {"status": "success", "symbol": index_symbol.upper(), "analysis": result}
        # Fallback basic stub
        return {
            "status": "success",
            "symbol": index_symbol.upper(),
            "analysis": {
                "strategy": "Bull Call Spread",
                "rationale": "Uptrend momentum with controlled risk; select near-the-money strikes",
                "legs": [
                    {"type": "BUY_CALL", "strike": "ATM", "expiry": "Nearest Weekly"},
                    {"type": "SELL_CALL", "strike": "ATM+200", "expiry": "Nearest Weekly"}
                ],
                "risk_reward": {"max_loss": "debit paid", "max_profit": "spread width - debit", "probability": "balanced"}
            }
        }
    except Exception as e:
        logger.error(f"Option chain AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New: P/L history (synthetic from overview positions)
@app.get("/api/dhan/pl/history")
async def pl_history(days: int = 7):
    if days < 1:
        days = 1
    if days > 90:
        days = 90
    try:
        # For now, synthesize a simple P/L curve using current overview snapshot and random walk
        # In a real system, we'd query historical snapshots from a datastore
        base_dt = datetime.utcnow()
        # Get current overview to approximate today's equity
        if dhan is None:
            raise HTTPException(status_code=503, detail="DhanProvider not available")
        overview = await dhan_overview()
        positions = overview.get("positions", [])
        holdings = overview.get("holdings", [])
        invested = sum([(p.get("invested") or 0) for p in positions]) + sum([(h.get("invested") or 0) for h in holdings])
        current = sum([(p.get("current_value") or 0) for p in positions]) + sum([(h.get("current_value") or 0) for h in holdings])
        today_equity = current or invested
        series = []
        equity = today_equity
        import random
        for i in range(days):
            dt = base_dt - timedelta(days=(days - 1 - i))
            # apply small daily change +/- 1%
            change = (random.random() - 0.5) * 0.02
            equity = max(0, equity * (1 + change))
            pnl = equity - invested
            pnl_pct = (pnl / invested * 100.0) if invested > 0 else 0.0
            series.append({
                "timestamp": dt.isoformat(),
                "equity": round(equity, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })
        return {"status": "success", "days": days, "series": series}
    except Exception as e:
        logger.error(f"P/L history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New: Backtesting endpoint (simple stub)
@app.get("/api/optionchain/backtest/{symbol}")
async def backtest_option_strategy(symbol: str, strategy: str = "bull_call_spread", days: int = 30):
    try:
        days = max(5, min(days, 180))
        base_dt = datetime.utcnow()
        equity = 100000.0
        curve = []
        import random
        wins = 0
        for i in range(days):
            dt = base_dt - timedelta(days=(days - 1 - i))
            # simplistic P/L drift
            daily_ret = (random.random() - 0.45) * 0.01  # slight positive drift
            equity *= (1 + daily_ret)
            if daily_ret > 0:
                wins += 1
            curve.append({"timestamp": dt.isoformat(), "equity": round(equity, 2)})
        total_return = (equity / 100000.0 - 1) * 100
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "strategy": strategy,
            "metrics": {
                "total_return_pct": round(total_return, 2),
                "win_rate_pct": round(wins / days * 100.0, 2),
                "max_drawdown_pct": round(5 + random.random() * 10, 2)
            },
            "equity_curve": curve
        }
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Engine A on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)