from fastapi import FastAPI, File, UploadFile, HTTPException
from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChartPatternDetector:
    """AI-powered chart pattern recognition for trading"""

    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = None
        self.model_path = model_path
        self.patterns = {
            0: "head_and_shoulders",
            1: "double_top",
            2: "double_bottom",
            3: "triangle_ascending",
            4: "triangle_descending",
            5: "wedge",
            6: "flag",
            7: "pennant",
            8: "cup_and_handle",
            9: "inverse_head_and_shoulders"
        }

    async def initialize(self):
        """Initialize the YOLO model"""
        if self.model is None:
            try:
                self.model = YOLO(self.model_path)
                logger.info("Chart pattern detection model initialized")
            except Exception as e:
                logger.error(f"Failed to initialize chart pattern model: {e}")
                raise

    async def detect_patterns(self, chart_image: bytes, filename: str = None) -> Dict:
        """Detect chart patterns in uploaded chart image"""
        try:
            await self.initialize()

            # Decode image
            nparr = np.frombuffer(chart_image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise HTTPException(status_code=400, detail="Invalid image format")

            # Run inference
            results = self.model(img)

            patterns_found = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())

                    if confidence > 0.5:  # Only high confidence detections
                        pattern_name = self.patterns.get(class_id, f"pattern_{class_id}")
                        patterns_found.append({
                            "pattern": pattern_name,
                            "confidence": float(confidence),
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "description": self._get_pattern_description(pattern_name)
                        })

            # Sort by confidence
            patterns_found.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "patterns_detected": patterns_found,
                "total_patterns": len(patterns_found),
                "analysis_timestamp": datetime.now().isoformat(),
                "recommendations": self._generate_trading_recommendations(patterns_found)
            }

        except Exception as e:
            logger.error(f"Error detecting chart patterns: {e}")
            raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")

    def _get_pattern_description(self, pattern: str) -> str:
        """Get description for detected pattern"""
        descriptions = {
            "head_and_shoulders": "Bearish reversal pattern - potential sell signal",
            "double_top": "Bearish reversal pattern - resistance at previous high",
            "double_bottom": "Bullish reversal pattern - support at previous low",
            "triangle_ascending": "Bullish continuation pattern - upward breakout expected",
            "triangle_descending": "Bearish continuation pattern - downward breakout expected",
            "wedge": "Reversal pattern depending on slope - analyze trend",
            "flag": "Bullish continuation pattern - consolidation before uptrend",
            "pennant": "Continuation pattern - breakout in direction of prior trend",
            "cup_and_handle": "Bullish continuation pattern - classic accumulation",
            "inverse_head_and_shoulders": "Bullish reversal pattern - potential buy signal"
        }
        return descriptions.get(pattern, f"Detected {pattern} pattern")

    def _generate_trading_recommendations(self, patterns: List[Dict]) -> List[str]:
        """Generate trading recommendations based on detected patterns"""
        if not patterns:
            return ["No significant patterns detected - monitor price action"]

        recommendations = []
        high_conf_patterns = [p for p in patterns if p["confidence"] > 0.7]

        if not high_conf_patterns:
            return ["Low confidence patterns detected - wait for confirmation"]

        # Analyze top pattern
        top_pattern = high_conf_patterns[0]
        pattern_name = top_pattern["pattern"]

        # Bullish patterns
        bullish_patterns = ["double_bottom", "triangle_ascending", "flag", "pennant", "cup_and_handle", "inverse_head_and_shoulders"]
        # Bearish patterns
        bearish_patterns = ["head_and_shoulders", "double_top", "triangle_descending"]

        if pattern_name in bullish_patterns:
            recommendations.append(f"🐂 BULLISH: {pattern_name.upper()} detected - Consider LONG positions")
            recommendations.append("Set stop loss below pattern support level")
            recommendations.append("Target profit at pattern height projection")
        elif pattern_name in bearish_patterns:
            recommendations.append(f"🐻 BEARISH: {pattern_name.upper()} detected - Consider SHORT positions")
            recommendations.append("Set stop loss above pattern resistance level")
            recommendations.append("Target profit at pattern height projection")
        else:
            recommendations.append(f"⚠️ NEUTRAL: {pattern_name.upper()} detected - Monitor for breakout direction")

        # Risk management
        recommendations.append("💰 Risk Management: Risk no more than 1-2% of capital per trade")
        recommendations.append("📊 Confirmation: Wait for volume spike on breakout")

        return recommendations

class TechnicalAnalysisAI:
    """AI-powered technical analysis service"""

    def __init__(self):
        self.pattern_detector = ChartPatternDetector()

    async def initialize(self):
        """Initialize all technical analysis components"""
        await self.pattern_detector.initialize()

    async def analyze_chart(self, chart_image: bytes, symbol: str = None) -> Dict:
        """Complete technical analysis of chart image"""
        try:
            # Detect patterns
            pattern_analysis = await self.pattern_detector.detect_patterns(chart_image)

            # Add symbol context if provided
            if symbol:
                pattern_analysis["symbol"] = symbol
                pattern_analysis["analysis_type"] = "chart_pattern_recognition"

            return pattern_analysis

        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {"error": str(e)}

    async def analyze_price_data(self, price_data: pd.DataFrame, symbol: str) -> Dict:
        """Analyze price data for patterns and indicators"""
        try:
            analysis = {
                "symbol": symbol,
                "analysis_timestamp": datetime.now().isoformat(),
                "price_analysis": {},
                "indicators": {},
                "signals": []
            }

            if len(price_data) < 20:
                return {"error": "Insufficient data for analysis"}

            # Basic price analysis
            analysis["price_analysis"] = {
                "current_price": price_data['close'].iloc[-1],
                "price_change_1d": ((price_data['close'].iloc[-1] - price_data['close'].iloc[-2]) / price_data['close'].iloc[-2]) * 100,
                "volatility_20d": price_data['close'].pct_change().rolling(20).std().iloc[-1] * 100,
                "volume_trend": "increasing" if price_data['volume'].iloc[-5:].mean() > price_data['volume'].iloc[-10:-5].mean() else "decreasing"
            }

            # Simple moving averages
            analysis["indicators"]["sma_20"] = price_data['close'].rolling(20).mean().iloc[-1]
            analysis["indicators"]["sma_50"] = price_data['close'].rolling(50).mean().iloc[-1]

            # RSI calculation
            def calculate_rsi(data, period=14):
                delta = data.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))

            analysis["indicators"]["rsi_14"] = calculate_rsi(price_data['close']).iloc[-1]

            # Generate signals
            current_price = price_data['close'].iloc[-1]
            sma_20 = analysis["indicators"]["sma_20"]
            sma_50 = analysis["indicators"]["sma_50"]
            rsi = analysis["indicators"]["rsi_14"]

            signals = []

            # Moving average signals
            if current_price > sma_20 > sma_50:
                signals.append({"type": "BULLISH", "signal": "Golden Cross", "strength": "Strong"})
            elif current_price < sma_20 < sma_50:
                signals.append({"type": "BEARISH", "signal": "Death Cross", "strength": "Strong"})

            # RSI signals
            if rsi > 70:
                signals.append({"type": "BEARISH", "signal": "Overbought (RSI > 70)", "strength": "Medium"})
            elif rsi < 30:
                signals.append({"type": "BULLISH", "signal": "Oversold (RSI < 30)", "strength": "Medium"})

            analysis["signals"] = signals

            return analysis

        except Exception as e:
            logger.error(f"Error in price data analysis: {e}")
            return {"error": str(e)}

# FastAPI app for technical analysis
app = FastAPI(title="Technical Analysis AI API")

tech_ai = TechnicalAnalysisAI()

@app.on_event("startup")
async def startup_event():
    await tech_ai.initialize()

@app.post("/analyze-chart")
async def analyze_chart(file: UploadFile = File(...), symbol: str = None):
    """Analyze chart image for patterns"""
    chart_data = await file.read()
    result = await tech_ai.analyze_chart(chart_data, symbol)
    return result

@app.post("/analyze-price-data")
async def analyze_price_data(price_data: Dict, symbol: str):
    """Analyze price data for technical indicators"""
    df = pd.DataFrame(price_data)
    result = await tech_ai.analyze_price_data(df, symbol)
    return result

@app.get("/")
async def root():
    return {"message": "Technical Analysis AI API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)