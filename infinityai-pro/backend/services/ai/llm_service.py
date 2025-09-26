# services/ai/llm_service.py
"""
InfinityAI.Pro - LLM Service
Local LLM integration using Ollama (LLaMA3, Mistral, etc.)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """Local LLM service using Ollama"""

    def __init__(self, config: Dict):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize Ollama connection"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.config['url'],
                timeout=self.config['timeout']
            )

            # Test connection
            await self._test_connection()
            self.initialized = True
            logger.info(f"✅ LLM Service initialized with model: {self.config['model']}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def _test_connection(self):
        """Test Ollama connection"""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            available_models = [model['name'] for model in data.get('models', [])]
            if self.config['model'] not in available_models:
                logger.warning(f"Model {self.config['model']} not found. Available: {available_models}")
            else:
                logger.info(f"Model {self.config['model']} is available")

        except Exception as e:
            logger.warning(f"Could not verify Ollama models: {e}")

    async def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Generate chat response"""
        try:
            if not self.initialized:
                raise RuntimeError("LLM service not initialized")

            # Build prompt with context
            system_prompt = "You are InfinityAI.Pro, an expert AI trading assistant. Provide clear, actionable insights for trading decisions."

            if context:
                system_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"

            payload = {
                "model": self.config['model'],
                "prompt": message,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 512
                }
            }

            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()

            return {
                "response": result.get("response", ""),
                "model": self.config['model'],
                "usage": {
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in LLM chat: {e}")
            return {"error": str(e)}

    async def generate_trading_strategy(self, signal_data: Dict, market_context: Dict = None) -> Dict:
        """Generate trading strategy analysis"""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            action = signal_data.get('direction', 'HOLD')
            score = signal_data.get('score', 0.0)

            prompt = f"""
            Analyze this trading signal and provide a comprehensive trading strategy:

            Signal Details:
            - Symbol: {symbol}
            - Recommended Action: {action}
            - Confidence Score: {score:.3f}
            - ML Probability: {signal_data.get('ml_prob', 0.0):.3f}
            - Rule Score: {signal_data.get('rule_score', 0.0):.3f}

            Market Context:
            {json.dumps(market_context, indent=2) if market_context else "No additional context"}

            Provide a structured analysis including:
            1. Strategy rationale
            2. Risk assessment (low/medium/high)
            3. Position sizing recommendation (as % of capital)
            4. Entry/exit points
            5. Stop loss and take profit levels
            6. Time horizon
            7. Key monitoring factors
            """

            response = await self.chat(prompt)

            # Parse response into structured format
            strategy = self._parse_strategy_response(response.get("response", ""), signal_data)

            return {
                "strategy": strategy,
                "raw_response": response,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating trading strategy: {e}")
            return {"error": str(e)}

    def _parse_strategy_response(self, response: str, signal_data: Dict) -> Dict:
        """Parse LLM response into structured strategy"""
        # Simple parsing - could be enhanced with better NLP
        lines = response.split('\n')

        strategy = {
            "symbol": signal_data.get('symbol', 'UNKNOWN'),
            "action": signal_data.get('direction', 'HOLD'),
            "confidence": signal_data.get('score', 0.0),
            "reasoning": response,
            "risk_level": "medium",
            "position_size": 0.02,  # 2% default
            "stop_loss": 0.03,
            "take_profit": 0.06,
            "time_horizon": "medium",
            "monitoring_points": []
        }

        # Extract key information from response
        for line in lines:
            line_lower = line.lower().strip()

            # Risk level
            if 'risk' in line_lower:
                if any(word in line_lower for word in ['low', 'minimal', 'small']):
                    strategy['risk_level'] = 'low'
                elif any(word in line_lower for word in ['high', 'significant', 'large']):
                    strategy['risk_level'] = 'high'

            # Position size
            if 'position' in line_lower and '%' in line:
                try:
                    import re
                    percent_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if percent_match:
                        strategy['position_size'] = float(percent_match.group(1)) / 100
                except:
                    pass

            # Stop loss
            if 'stop' in line_lower and '%' in line:
                try:
                    import re
                    sl_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if sl_match:
                        strategy['stop_loss'] = float(sl_match.group(1)) / 100
                except:
                    pass

            # Monitoring points
            if any(keyword in line_lower for keyword in ['monitor', 'watch', 'key', 'important']):
                strategy['monitoring_points'].append(line.strip())

        return strategy

    async def health_check(self) -> Dict:
        """Check LLM service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            # Quick test
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            return {
                "status": "healthy",
                "model": self.config['model'],
                "url": self.config['url']
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }