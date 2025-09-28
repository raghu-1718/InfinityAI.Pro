# services/ai/llm_service.py
"""
InfinityAI.Pro - Multi-Cloud LLM Service
Supports RunPod (primary), Azure OpenAI (secondary), AWS Bedrock (tertiary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import os
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """Multi-cloud LLM service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize multi-cloud LLM connections"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            self.initialized = True
            logger.info("✅ Multi-cloud LLM Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Azure OpenAI (Primary)
    async def azure_ask(self, prompt: str, **kwargs) -> str:
        """Azure OpenAI inference"""
        try:
            azure_url = f"{self.config.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.config.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview"
            headers = {
                "api-key": self.config.AZURE_OPENAI_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "messages": [
                    {"role": "system", "content": "You are InfinityAI.Pro, an expert AI trading assistant with deep knowledge of financial markets, technical analysis, and risk management."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get("max_tokens", 1024),
                "temperature": kwargs.get("temperature", 0.3),
                "top_p": kwargs.get("top_p", 0.9),
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            raise

    async def azure_generate(self, prompt: str, **kwargs) -> str:
        """Azure text generation"""
        return await self.azure_ask(prompt, **kwargs)

    # AWS Bedrock (Secondary)
    async def aws_ask(self, prompt: str, **kwargs) -> str:
        """AWS Bedrock inference"""
        try:
            import boto3
            bedrock = boto3.client(
                'bedrock-runtime',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get("max_tokens", 1024),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", 0.3),
                "top_p": kwargs.get("top_p", 0.9)
            }

            response = bedrock.invoke_model(
                modelId=self.config.AWS_BEDROCK_MODEL_ID,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )

            result = json.loads(response["body"].read())
            return result.get("content", [{}])[0].get("text", "")

        except Exception as e:
            logger.error(f"AWS Bedrock error: {e}")
            raise

    async def aws_generate(self, prompt: str, **kwargs) -> str:
        """AWS text generation"""
        return await self.aws_ask(prompt, **kwargs)

    # Legacy methods for backward compatibility
    async def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Generate chat response using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                response = await router.ask_llm(message)

            return {
                "response": response,
                "model": "multi-cloud-failover",
                "usage": {"tokens": len(response.split())},
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in LLM chat: {e}")
            return {"error": str(e)}

    async def generate_trading_strategy(self, signal_data: Dict, market_context: Dict = None) -> Dict:
        """Generate trading strategy analysis using router"""
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

            from .router import AIRouter
            async with AIRouter() as router:
                response = await router.ask_llm(prompt)

            # Parse response into structured format
            strategy = self._parse_strategy_response(response, signal_data)

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

            # Check all providers
            from .router import AIRouter
            async with AIRouter() as router:
                health_status = await router.get_health_status()

            return {
                "status": "healthy",
                "providers": health_status,
                "multi_cloud": True,
                "primary_provider": "azure",
                "secondary_provider": "aws"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }