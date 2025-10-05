"""
Real-time AI Analysis API - Enhanced with Dhan Integration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from services.ai_trading_engine import ai_trading_engine
from services.dhan_api_service import dhan_api_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-analysis", tags=["AI Real-time Analysis"])

class AnalysisRequest(BaseModel):
    symbols: List[str]
    analysis_type: Optional[str] = "comprehensive"
    include_opportunities: Optional[bool] = True

class AnalysisResponse(BaseModel):
    success: bool
    timestamp: str
    symbols_analyzed: int
    market_overview: Dict[str, Any]
    symbol_analyses: Dict[str, Any]
    top_opportunities: List[Dict[str, Any]]
    data_source: str
    real_data: bool

@router.post("/comprehensive", response_model=AnalysisResponse)
async def comprehensive_analysis(request: AnalysisRequest):
    """
    🧠 Comprehensive AI analysis with real-time Dhan data
    
    Features:
    - Real-time market data from Dhan API
    - Technical analysis with trend detection
    - Sentiment analysis and market psychology
    - Risk assessment and volatility analysis
    - AI-powered trading recommendations
    - Trading opportunity identification
    - Market overview and insights
    """
    
    try:
        logger.info(f"🚀 Starting comprehensive AI analysis for {len(request.symbols)} symbols")
        
        # Validate symbols
        if not request.symbols or len(request.symbols) > 20:
            raise HTTPException(status_code=400, detail="Please provide 1-20 symbols")
        
        # Perform AI analysis
        result = await ai_trading_engine.analyze_symbols(request.symbols)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
        
        return AnalysisResponse(
            success=True,
            timestamp=result["timestamp"],
            symbols_analyzed=result["symbols_analyzed"],
            market_overview=result["market_overview"],
            symbol_analyses=result["symbol_analyses"],
            top_opportunities=result["top_opportunities"] if request.include_opportunities else [],
            data_source=result["data_source"],
            real_data=result["real_data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-pulse")
async def get_market_pulse():
    """
    📊 Quick market pulse analysis
    
    Analyzes key market indices for overall market sentiment
    """
    
    try:
        # Analyze key indices
        key_symbols = ["NIFTY", "BANKNIFTY", "SENSEX", "NIFTYIT", "NIFTYPHARMA"]
        
        result = await ai_trading_engine.analyze_symbols(key_symbols)
        
        if not result.get("success"):
            return {"success": False, "error": "Market pulse unavailable"}
        
        market_overview = result["market_overview"]
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "market_pulse": {
                "overall_sentiment": market_overview["market_sentiment"],
                "bullish_count": market_overview["bullish_count"],
                "bearish_count": market_overview["bearish_count"],
                "confidence": market_overview["average_confidence"],
                "opportunities": market_overview["opportunities_count"],
                "recommendation": market_overview["recommendation"],
                "status": "ACTIVE" if market_overview["opportunities_count"] > 0 else "WAITING"
            },
            "indices_analyzed": key_symbols,
            "data_source": result["data_source"]
        }
        
    except Exception as e:
        logger.error(f"Market pulse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbol/{symbol}")
async def analyze_single_symbol(symbol: str):
    """
    🎯 Deep analysis of a single symbol
    
    Provides detailed technical, sentiment, and risk analysis for one symbol
    """
    
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        result = await ai_trading_engine.analyze_symbols([symbol.upper()])
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Symbol analysis failed")
        
        symbol_data = result["symbol_analyses"].get(symbol.upper())
        
        if not symbol_data:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "analysis": symbol_data,
            "market_context": result["market_overview"],
            "timestamp": datetime.now().isoformat(),
            "data_source": result["data_source"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single symbol analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities")
async def get_trading_opportunities():
    """
    💰 Current high-confidence trading opportunities
    
    Returns only the best trading opportunities with high confidence scores
    """
    
    try:
        # Analyze a broad set of popular symbols
        popular_symbols = [
            "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK", 
            "INFY", "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC"
        ]
        
        result = await ai_trading_engine.analyze_symbols(popular_symbols)
        
        if not result.get("success"):
            return {"success": False, "error": "Opportunities analysis failed"}
        
        opportunities = result["top_opportunities"]
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "opportunities_found": len(opportunities),
            "top_opportunities": opportunities,
            "market_summary": {
                "sentiment": result["market_overview"]["market_sentiment"],
                "confidence": result["market_overview"]["average_confidence"],
                "recommendation": result["market_overview"]["recommendation"]
            },
            "symbols_scanned": len(popular_symbols),
            "data_source": result["data_source"]
        }
        
    except Exception as e:
        logger.error(f"Opportunities analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors")
async def analyze_sectors():
    """
    🏭 Sector-wise analysis and comparison
    
    Analyzes different sectors to identify the strongest performing areas
    """
    
    try:
        # Define sector representatives
        sectors = {
            "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK"],
            "IT": ["TCS", "INFY", "WIPRO", "HCLTECH"],
            "Energy": ["RELIANCE", "ONGC", "BPCL"],
            "Auto": ["MARUTI", "BAJAJFINSV", "M&M"],
            "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA"]
        }
        
        sector_analyses = {}
        
        for sector_name, symbols in sectors.items():
            try:
                result = await ai_trading_engine.analyze_symbols(symbols)
                
                if result.get("success"):
                    overview = result["market_overview"]
                    sector_analyses[sector_name] = {
                        "sentiment": overview["market_sentiment"],
                        "confidence": overview["average_confidence"],
                        "opportunities": overview["opportunities_count"],
                        "bullish_stocks": overview["bullish_count"],
                        "total_stocks": overview["total_symbols"],
                        "recommendation": overview["recommendation"]
                    }
                    
            except Exception as e:
                logger.error(f"Sector analysis error for {sector_name}: {e}")
                sector_analyses[sector_name] = {"error": "Analysis failed"}
        
        # Find best performing sector
        best_sector = None
        best_score = -1
        
        for sector, data in sector_analyses.items():
            if "error" not in data:
                score = data["confidence"] * (data["opportunities"] + 1)
                if score > best_score:
                    best_score = score
                    best_sector = sector
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "sectors_analyzed": list(sectors.keys()),
            "sector_analyses": sector_analyses,
            "best_performing_sector": best_sector,
            "market_leaders": {
                "most_bullish": max(sector_analyses.items(), 
                                  key=lambda x: x[1].get("bullish_stocks", 0) if "error" not in x[1] else 0,
                                  default=(None, {}))[0],
                "most_opportunities": max(sector_analyses.items(),
                                        key=lambda x: x[1].get("opportunities", 0) if "error" not in x[1] else 0,
                                        default=(None, {}))[0]
            }
        }
        
    except Exception as e:
        logger.error(f"Sector analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_analysis_status():
    """
    ⚡ Get AI analysis system status and capabilities
    """
    
    try:
        # Test Dhan API connectivity
        test_result = await dhan_api_service.get_live_quote(["NIFTY"])
        dhan_status = test_result.get("success", False)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "ai_engine": "operational",
                "dhan_api": "connected" if dhan_status else "disconnected",
                "real_time_data": dhan_status,
                "analysis_features": [
                    "Technical Analysis",
                    "Sentiment Analysis", 
                    "Risk Assessment",
                    "AI Recommendations",
                    "Trading Opportunities",
                    "Market Overview",
                    "Sector Analysis"
                ]
            },
            "capabilities": {
                "max_symbols_per_request": 20,
                "analysis_types": ["comprehensive", "technical", "sentiment"],
                "supported_exchanges": ["NSE", "BSE"],
                "update_frequency": "real-time",
                "confidence_threshold": ai_trading_engine.confidence_threshold
            },
            "data_sources": {
                "primary": "Dhan API" if dhan_status else "Mock Data",
                "backup": "Algorithmic Generation",
                "real_time": dhan_status
            }
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))