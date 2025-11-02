#!/usr/bin/env python3
"""
AI Analysis Fallback Service
============================
Provides fallback AI analysis when main services are unavailable.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class AIAnalysisFallback(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/gemini-analysis':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "market_sentiment": "NEUTRAL",
                "confidence": 0.75,
                "key_insights": [
                    "Market in consolidation phase",
                    "Awaiting key economic indicators", 
                    "Technical levels holding support"
                ],
                "recommendations": [
                    "Monitor key resistance levels",
                    "Watch for volume confirmation",
                    "Maintain risk management"
                ],
                "status": "fallback_service"
            }
            
            self.wfile.write(json.dumps(analysis).encode())
            
        elif self.path == '/vertex-analysis':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "model_predictions": {
                    "nifty_direction": "NEUTRAL",
                    "probability": 0.65,
                    "target_range": "22500-23000",
                    "timeframe": "5-day"
                },
                "sector_analysis": {
                    "banking": "NEUTRAL",
                    "it": "POSITIVE", 
                    "pharma": "NEUTRAL",
                    "metals": "NEGATIVE"
                },
                "status": "fallback_service"
            }
            
            self.wfile.write(json.dumps(analysis).encode())
            
        else:
            self.send_response(404)
            self.end_headers()

def run_fallback_service(port=8888):
    server = HTTPServer(('localhost', port), AIAnalysisFallback)
    print(f"🤖 AI Analysis Fallback Service running on port {port}")
    print("Available endpoints:")
    print(f"  - http://localhost:{port}/gemini-analysis")
    print(f"  - http://localhost:{port}/vertex-analysis")
    server.serve_forever()

if __name__ == "__main__":
    run_fallback_service()
