"""
InfinityAI.Pro - Engine A: Data Ingestion & Preprocessing
Handles market data feeds, news sentiment, and data preprocessing
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import httpx
import pandas as pd
import numpy as np
from pydantic import BaseModel
import websockets
import redis
# from kafka import KafkaProducer
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InfinityAI Engine A - Data Ingestion", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MARKET_DATA_TOPIC = "market_data"
NEWS_TOPIC = "news_sentiment"

# Initialize connections
redis_client = redis.from_url(REDIS_URL)
# kafka_producer = KafkaProducer(
#     bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )

class MarketDataRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1min"
    limit: int = 100

class NewsRequest(BaseModel):
    query: str
    limit: int = 20

class DataProcessingStatus(BaseModel):
    status: str
    processed_records: int
    timestamp: datetime

class MarketDataService:
    """Handles real-time and historical market data"""
    
    def __init__(self):
        self.active_streams = {}
        
    async def get_historical_data(self, symbols: List[str], timeframe: str = "1min", limit: int = 100) -> Dict:
        """Fetch historical market data"""
        try:
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval=timeframe)
                
                if not hist.empty:
                    data[symbol] = {
                        "timestamp": hist.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        "open": hist['Open'].tolist(),
                        "high": hist['High'].tolist(),
                        "low": hist['Low'].tolist(),
                        "close": hist['Close'].tolist(),
                        "volume": hist['Volume'].tolist()
                    }
                    
                    # Cache in Redis
                    redis_key = f"market_data:{symbol}:{timeframe}"
                    redis_client.setex(redis_key, 300, json.dumps(data[symbol]))
                    
                    # Send to Kafka for real-time processing
# kafka_producer.send(MARKET_DATA_TOPIC, {
                    #     "symbol": symbol,
                    #     "data": data[symbol],
                    #     "timestamp": datetime.now(timezone.utc).isoformat()
                    # })
                    
            logger.info(f"Fetched historical data for {len(symbols)} symbols")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def start_realtime_stream(self, symbols: List[str]):
        """Start real-time data streaming"""
        try:
            # This would connect to actual broker APIs in production
            # For now, we simulate with periodic updates
            
            async def stream_data():
                while True:
                    for symbol in symbols:
                        # Simulate real-time price updates
                        current_price = np.random.uniform(100, 200)
                        volume = np.random.randint(1000, 50000)
                        
                        market_update = {
                            "symbol": symbol,
                            "price": current_price,
                            "volume": volume,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "realtime_tick"
                        }
                        
                        # Send to Kafka
# kafka_producer.send(MARKET_DATA_TOPIC, market_update)
                        
                        # Cache latest price
                        redis_client.setex(f"price:{symbol}", 60, current_price)
                        
                    await asyncio.sleep(1)  # 1-second intervals
            
            # Start background task
            task = asyncio.create_task(stream_data())
            self.active_streams["-".join(symbols)] = task
            
            return {"status": "started", "symbols": symbols}
            
        except Exception as e:
            logger.error(f"Error starting realtime stream: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class NewsService:
    """Handles news data and sentiment analysis"""
    
    async def fetch_news(self, query: str, limit: int = 20) -> Dict:
        """Fetch news articles and perform basic sentiment analysis"""
        try:
            # In production, this would connect to news APIs (Alpha Vantage, News API, etc.)
            # For demo, we simulate news data
            
            news_items = []
            for i in range(limit):
                news_item = {
                    "id": f"news_{i}",
                    "title": f"Market Update: {query} shows positive momentum",
                    "summary": f"Analysis of {query} indicates bullish sentiment with increased trading volume.",
                    "sentiment_score": np.random.uniform(-1, 1),
                    "relevance_score": np.random.uniform(0.5, 1),
                    "source": "MarketWatch",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "url": f"https://marketwatch.com/article/{i}"
                }
                news_items.append(news_item)
                
                # Send to Kafka
# kafka_producer.send(NEWS_TOPIC, news_item)
            
            # Cache news data
            cache_key = f"news:{query}"
            redis_client.setex(cache_key, 1800, json.dumps(news_items))  # 30 minutes
            
            logger.info(f"Fetched {len(news_items)} news items for query: {query}")
            return {"status": "success", "count": len(news_items), "data": news_items}
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class DataProcessor:
    """Handles data preprocessing and feature engineering"""
    
    def preprocess_market_data(self, raw_data: Dict) -> Dict:
        """Apply technical indicators and preprocessing"""
        try:
            processed_data = {}
            
            for symbol, data in raw_data.items():
                df = pd.DataFrame(data)
                
                if 'close' in df.columns:
                    # Calculate technical indicators
                    df['sma_20'] = df['close'].rolling(window=20).mean()
                    df['sma_50'] = df['close'].rolling(window=50).mean()
                    df['rsi'] = self.calculate_rsi(df['close'])
                    df['macd'] = self.calculate_macd(df['close'])
                    df['volume_sma'] = df['volume'].rolling(window=10).mean() if 'volume' in df.columns else 0
                    
                    # Feature engineering
                    df['price_change'] = df['close'].pct_change()
                    df['volatility'] = df['close'].rolling(window=20).std()
                    df['volume_ratio'] = df['volume'] / df['volume_sma'] if 'volume' in df.columns else 1
                    
                    processed_data[symbol] = df.fillna(0).to_dict('records')
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return {}
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD indicator"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        return macd

# Initialize services
market_data_service = MarketDataService()
news_service = NewsService()
data_processor = DataProcessor()

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Engine A - Data Ingestion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@app.post("/market-data/historical")
async def get_historical_data(request: MarketDataRequest):
    """Get historical market data"""
    return await market_data_service.get_historical_data(
        symbols=request.symbols,
        timeframe=request.timeframe,
        limit=request.limit
    )

@app.post("/market-data/stream/start")
async def start_market_stream(request: MarketDataRequest):
    """Start real-time market data streaming"""
    return await market_data_service.start_realtime_stream(request.symbols)

@app.post("/news/fetch")
async def fetch_news(request: NewsRequest):
    """Fetch news articles and sentiment"""
    return await news_service.fetch_news(
        query=request.query,
        limit=request.limit
    )

@app.post("/data/preprocess")
async def preprocess_data(raw_data: Dict):
    """Preprocess and engineer features from raw market data"""
    processed_data = data_processor.preprocess_market_data(raw_data)
    
    return {
        "status": "success",
        "processed_symbols": list(processed_data.keys()),
        "data": processed_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/data/cache/{symbol}")
async def get_cached_data(symbol: str):
    """Get cached market data for a symbol"""
    try:
        price_key = f"price:{symbol}"
        data_key = f"market_data:{symbol}:1min"
        
        current_price = redis_client.get(price_key)
        historical_data = redis_client.get(data_key)
        
        return {
            "symbol": symbol,
            "current_price": float(current_price) if current_price else None,
            "historical_data": json.loads(historical_data) if historical_data else None,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get Engine A status and metrics"""
    try:
        # Check Redis connection
        redis_status = "connected" if redis_client.ping() else "disconnected"
        
        # Get active streams count
        active_streams = len(market_data_service.active_streams)
        
        return {
            "service": "Engine A - Data Ingestion",
            "status": "operational",
            "redis_status": redis_status,
            "active_streams": active_streams,
            "processed_records": 0,  # This would be tracked in production
            "uptime": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "service": "Engine A - Data Ingestion",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
