# 🚀 InfinityAI.Pro - Backend with Ultra Aggressive Trading Integration
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import uvicorn
import os
from datetime import datetime
import json

# Import our ultra aggressive trader
from ultra_aggressive_trader import UltraAggressiveTrader

app = FastAPI(
    title="InfinityAI.Pro - Ultra Aggressive Trading",
    description="Maximum Aggression Trading Platform - NO CONFIRMATIONS",
    version="3.0.0"
)

# Initialize ultra aggressive trading system
ultra_trader = UltraAggressiveTrader()

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the ultra aggressive trading dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>InfinityAI.Pro - Ultra Aggressive Trading</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: 'Courier New', monospace; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                min-height: 100vh;
            }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .status-card { 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            .aggressive { background: linear-gradient(45deg, #ff416c, #ff4b2b); }
            .profit { background: linear-gradient(45deg, #56ab2f, #a8e6cf); }
            .control { background: linear-gradient(45deg, #667eea, #764ba2); }
            .stats { background: linear-gradient(45deg, #ffecd2, #fcb69f); color: #333; }
            h1 { color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
            .btn { 
                display: inline-block; 
                padding: 12px 25px; 
                margin: 10px; 
                background: #ff4b2b; 
                color: white; 
                text-decoration: none; 
                border-radius: 25px;
                transition: all 0.3s;
                border: none;
                cursor: pointer;
                font-weight: bold;
            }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
            .api-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .api-link { 
                display: block; 
                padding: 15px; 
                background: rgba(255,255,255,0.1); 
                border-radius: 10px; 
                text-decoration: none; 
                color: white;
                transition: all 0.3s;
            }
            .api-link:hover { background: rgba(255,255,255,0.2); transform: scale(1.05); }
            .live-indicator { 
                width: 15px; 
                height: 15px; 
                background: #00ff00; 
                border-radius: 50%; 
                display: inline-block; 
                animation: pulse 2s infinite;
            }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .warning { 
                background: linear-gradient(45deg, #ff6b6b, #ffa500); 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0;
                text-align: center;
                font-weight: bold;
            }
        </style>
        <script>
            function refreshStatus() {
                fetch('/api/aggressive/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('capital').innerText = '₹' + data.current_capital.toFixed(2);
                        document.getElementById('target').innerText = '₹' + data.target_capital.toFixed(2);
                        document.getElementById('progress').innerText = ((data.current_capital/data.target_capital)*100).toFixed(1) + '%';
                        document.getElementById('opportunities').innerText = data.opportunities_count;
                    })
                    .catch(err => console.log('Status update failed:', err));
            }
            
            setInterval(refreshStatus, 5000); // Update every 5 seconds
            window.onload = refreshStatus;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔥 InfinityAI.Pro - Ultra Aggressive Trading</h1>
                <p><span class="live-indicator"></span> LIVE SYSTEM - ZERO CONFIRMATIONS - IMMEDIATE EXECUTION</p>
            </div>
            
            <div class="warning">
                🚨 ULTRA AGGRESSIVE MODE ACTIVE 🚨<br>
                NO CONFIRMATIONS • IMMEDIATE EXECUTION • MAXIMUM RISK/REWARD
            </div>
            
            <div class="status-grid">
                <div class="status-card aggressive">
                    <h2>🔥 AGGRESSIVE STATUS</h2>
                    <p>✅ Ultra Aggressive Mode: ACTIVE</p>
                    <p>✅ Immediate Execution: ENABLED</p>
                    <p>✅ Zero Confirmations: ACTIVE</p>
                    <p>✅ Capital Doubling: TARGET SET</p>
                    <p>⚡ Scan Interval: 30 seconds</p>
                    <p>🎯 Confidence Threshold: 65%</p>
                </div>
                
                <div class="status-card profit">
                    <h2>💰 CAPITAL STATUS</h2>
                    <p>Current Capital: <span id="capital">Loading...</span></p>
                    <p>Target Capital: <span id="target">Loading...</span></p>
                    <p>Progress: <span id="progress">Loading...</span></p>
                    <p>Max Position Size: 80%</p>
                    <p>Aggression Multiplier: 3x</p>
                </div>
                
                <div class="status-card control">
                    <h2>🚀 TRADING CONTROLS</h2>
                    <div class="api-grid">
                        <a href="/api/aggressive/start" class="btn">START AGGRESSIVE</a>
                        <a href="/api/aggressive/stop" class="btn">STOP TRADING</a>
                        <a href="/api/aggressive/status" class="btn">VIEW STATUS</a>
                        <a href="/api/aggressive/execute" class="btn">FORCE EXECUTE</a>
                    </div>
                </div>
                
                <div class="status-card stats">
                    <h2>📊 LIVE STATS</h2>
                    <p>Active Opportunities: <span id="opportunities">Loading...</span></p>
                    <p>Trades Executed: <span id="trades">0</span></p>
                    <p>Success Rate: <span id="success">0%</span></p>
                    <p>Avg Profit: <span id="avg_profit">0%</span></p>
                </div>
            </div>
            
            <div class="status-card control" style="margin-top: 20px;">
                <h2>🌐 API ENDPOINTS</h2>
                <div class="api-grid">
                    <a href="/api/aggressive/status" class="api-link">📊 Current Status</a>
                    <a href="/api/aggressive/opportunities" class="api-link">🎯 Live Opportunities</a>
                    <a href="/api/aggressive/positions" class="api-link">📈 Active Positions</a>
                    <a href="/api/aggressive/trades" class="api-link">📋 Trade History</a>
                    <a href="/api/aggressive/start" class="api-link">🚀 Start Trading</a>
                    <a href="/api/aggressive/execute" class="api-link">⚡ Force Execute</a>
                </div>
            </div>
            
            <div class="status-card aggressive" style="margin-top: 20px;">
                <h2>⚡ ULTRA AGGRESSIVE FEATURES</h2>
                <p>🔥 Real-time opportunity scanning every 30 seconds</p>
                <p>⚡ Immediate order execution with no confirmations</p>
                <p>💰 Progressive position sizing up to 80% capital</p>
                <p>📈 Aggressive trailing stops (8% start, 4% trail)</p>
                <p>🎯 Capital doubling algorithms with 100% target</p>
                <p>🚀 Multi-asset momentum detection (NIFTY, Bank NIFTY, Crude)</p>
                <p>🔄 Automatic stop loss at 25% (high risk, high reward)</p>
                <p>📊 Real-time P&L monitoring and position management</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/api/aggressive/status")
async def get_aggressive_status():
    """Get ultra aggressive trading status"""
    try:
        current_capital = await ultra_trader.get_available_funds()
        opportunities = await ultra_trader.scan_aggressive_opportunities()
        
        return {
            "status": "ultra_aggressive_active",
            "timestamp": datetime.now().isoformat(),
            "current_capital": current_capital,
            "target_capital": ultra_trader.target_capital,
            "progress_percent": (current_capital / ultra_trader.target_capital * 100) if ultra_trader.target_capital > 0 else 0,
            "opportunities_count": len(opportunities),
            "executed_trades": len(ultra_trader.executed_trades),
            "scan_interval": ultra_trader.scan_interval,
            "confidence_threshold": ultra_trader.confidence_threshold,
            "max_position_size": ultra_trader.max_position_size,
            "immediate_execution": ultra_trader.immediate_execution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aggressive/opportunities")
async def get_opportunities():
    """Get current aggressive opportunities"""
    try:
        opportunities = await ultra_trader.scan_aggressive_opportunities()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/aggressive/execute")
async def force_execute():
    """Force execute best opportunity immediately"""
    try:
        opportunities = await ultra_trader.scan_aggressive_opportunities()
        
        if not opportunities:
            return {"status": "no_opportunities", "message": "No opportunities found"}
        
        best_opportunity = opportunities[0]
        success = await ultra_trader.execute_immediate_order(best_opportunity)
        
        return {
            "status": "success" if success else "failed",
            "timestamp": datetime.now().isoformat(),
            "executed_opportunity": best_opportunity if success else None,
            "message": "Order executed immediately" if success else "Execution failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aggressive/positions")
async def get_positions():
    """Get current positions"""
    try:
        # This would call the Dhan API to get positions
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Position data would be here"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aggressive/trades")
async def get_trade_history():
    """Get executed trade history"""
    try:
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "executed_trades": ultra_trader.executed_trades,
            "total_trades": len(ultra_trader.executed_trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/aggressive/start")
async def start_aggressive_trading(background_tasks: BackgroundTasks):
    """Start ultra aggressive trading in background"""
    try:
        background_tasks.add_task(ultra_trader.aggressive_capital_doubling_cycle)
        return {
            "status": "started",
            "timestamp": datetime.now().isoformat(),
            "message": "Ultra aggressive trading started in background",
            "mode": "zero_confirmations_immediate_execution"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "ultra_aggressive_ready",
        "timestamp": datetime.now().isoformat(),
        "service": "InfinityAI.Pro Ultra Aggressive Trading",
        "version": "3.0.0",
        "mode": "immediate_execution_no_confirmations"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize ultra aggressive trading on startup"""
    print("🔥 InfinityAI.Pro Ultra Aggressive Trading System Starting...")
    print("⚡ ZERO CONFIRMATIONS - IMMEDIATE EXECUTION")
    print("🎯 GOAL: DOUBLE CAPITAL THROUGH MAXIMUM AGGRESSION")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )