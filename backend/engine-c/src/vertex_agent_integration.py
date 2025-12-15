"""
Vertex AI Agent Engine Integration for InfinityAI.Pro
Integrates the Financial Advisor Agent for real-time AI-driven trade analysis and execution.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import httpx
from google.auth import default
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class AgentAnalysisType(Enum):
    """Types of agent analysis requests"""
    MARKET_ANALYSIS = "market_analysis"
    TRADE_RECOMMENDATION = "trade_recommendation"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_REVIEW = "portfolio_review"
    ENTRY_EXIT_TIMING = "entry_exit_timing"
    STRATEGY_EVALUATION = "strategy_evaluation"


class TradeAction(Enum):
    """Trade action recommendations"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    WAIT = "WAIT"


class VertexAgentIntegration:
    """
    Integrates Vertex AI Agent Engine (Financial Advisor) with InfinityAI.Pro
    for real-time AI-driven trade analysis and automated execution.
    """

    def __init__(self, firestore_db=None):
        self.db = firestore_db
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")
        self.region = "us-central1"
        self.agent_engine_id = "8753627684120035328"  # Financial Advisor Agent
        self.agent_engine_name = f"projects/{self.project_id}/locations/{self.region}/reasoningEngines/{self.agent_engine_id}"

        # API endpoints
        self.base_url = f"https://{self.region}-aiplatform.googleapis.com/v1"
        self.query_url = f"{self.base_url}/{self.agent_engine_name}:query"
        self.stream_url = f"{self.base_url}/{self.agent_engine_name}:streamQuery"

        # Engine URLs for integration
        self.engine_b_url = os.environ.get("ENGINE_B_URL", "https://engine-b.infinityai.pro")

        # Auth
        self._credentials = None
        self._token = None
        self._token_expiry = None

        self._initialized = False
        logger.info(f"✅ VertexAgentIntegration initialized for agent: {self.agent_engine_id}")

    def initialize(self, firestore_db):
        """Initialize with Firestore database"""
        self.db = firestore_db
        self._initialized = True
        logger.info("✅ VertexAgentIntegration connected to Firestore")

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self.db is not None

    async def _get_access_token(self) -> str:
        """Get Google Cloud access token for API calls"""
        try:
            # Check if token is still valid
            if self._token and self._token_expiry and datetime.utcnow() < self._token_expiry:
                return self._token

            # Get new credentials
            credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

            # Refresh credentials
            request = Request()
            credentials.refresh(request)

            self._token = credentials.token
            self._token_expiry = datetime.utcnow() + timedelta(minutes=55)  # Tokens last 60 min

            return self._token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_agent_session(self, user_id: str, initial_state: Dict = None) -> Dict[str, Any]:
        """Create a new session with the Financial Advisor Agent"""
        try:
            token = await self._get_access_token()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.query_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "class_method": "create_session",
                        "input": {
                            "user_id": user_id,
                            "state": initial_state or {}
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    session_id = result.get("output", {}).get("id")

                    # Store session mapping in Firestore
                    if self.db and session_id:
                        self.db.collection("agent_sessions").document(user_id).set({
                            "agent_session_id": session_id,
                            "created_at": datetime.utcnow().isoformat(),
                            "last_query": None,
                            "query_count": 0
                        }, merge=True)

                    logger.info(f"✅ Created agent session {session_id} for user {user_id}")
                    return {"success": True, "session_id": session_id}
                else:
                    logger.error(f"Failed to create session: {response.text}")
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error creating agent session: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_session(self, user_id: str) -> Optional[str]:
        """Get existing session ID for user, or create new one"""
        try:
            if self.db:
                doc = self.db.collection("agent_sessions").document(user_id).get()
                if doc.exists:
                    return doc.to_dict().get("agent_session_id")

            # Create new session if none exists
            result = await self.create_agent_session(user_id)
            return result.get("session_id") if result.get("success") else None

        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None

    # =========================================================================
    # AI Analysis & Trade Recommendations
    # =========================================================================

    async def analyze_trade_opportunity(
        self,
        user_id: str,
        symbol: str,
        current_price: float,
        market_data: Dict[str, Any] = None,
        portfolio_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze a trade opportunity using the Financial Advisor Agent.
        Returns actionable trade recommendation with timing.
        """
        try:
            session_id = await self.get_user_session(user_id)
            if not session_id:
                return {"success": False, "error": "Could not get agent session"}

            # Build comprehensive analysis prompt
            prompt = self._build_analysis_prompt(
                symbol=symbol,
                current_price=current_price,
                market_data=market_data,
                portfolio_context=portfolio_context
            )

            # Query the agent
            result = await self._query_agent(user_id, session_id, prompt)

            if result.get("success"):
                # Parse agent response into structured recommendation
                recommendation = self._parse_trade_recommendation(result.get("response", ""))

                # Log the analysis
                if self.db:
                    self.db.collection("agent_analyses").add({
                        "user_id": user_id,
                        "symbol": symbol,
                        "current_price": current_price,
                        "recommendation": recommendation,
                        "raw_response": result.get("response", "")[:1000],
                        "timestamp": datetime.utcnow().isoformat()
                    })

                return {
                    "success": True,
                    "symbol": symbol,
                    "current_price": current_price,
                    "recommendation": recommendation,
                    "agent_response": result.get("response"),
                    "model": result.get("model", "gemini-2.5-pro"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error analyzing trade opportunity: {e}")
            return {"success": False, "error": str(e)}

    async def get_realtime_trade_signal(
        self,
        user_id: str,
        symbol: str,
        timeframe: str = "intraday"
    ) -> Dict[str, Any]:
        """
        Get real-time trade signal from AI Agent combined with Engine B analysis.
        This is the main entry point for automated trading decisions.
        """
        try:
            # Step 1: Get Engine B technical analysis
            engine_b_signal = await self._get_engine_b_signal(symbol, timeframe)

            # Step 2: Get current market pulse
            market_pulse = await self._get_market_pulse()

            # Step 3: Query Financial Advisor Agent for strategic analysis
            session_id = await self.get_user_session(user_id)

            combined_prompt = f"""
            REAL-TIME TRADE ANALYSIS REQUEST for {symbol}:

            Technical Analysis from ML Models:
            - Signal: {engine_b_signal.get('signal', 'N/A')}
            - Confidence: {engine_b_signal.get('confidence', 0)}%
            - RSI: {engine_b_signal.get('analysis', {}).get('rsi', 'N/A')}
            - MACD: {engine_b_signal.get('analysis', {}).get('macd', 'N/A')}
            - Trend: {engine_b_signal.get('analysis', {}).get('trend', 'N/A')}

            Market Conditions:
            - NIFTY: {market_pulse.get('indices', {}).get('nifty', {}).get('change_percent', 0)}%
            - Market Status: {market_pulse.get('market_status', {}).get('status', 'N/A')}
            - Overall Signal: {market_pulse.get('overall_signal', 'N/A')}

            Based on this data, provide:
            1. Should we execute a trade NOW? (YES/NO/WAIT)
            2. If YES, what action? (BUY/SELL)
            3. Entry price recommendation
            4. Stop loss level
            5. Target prices (T1, T2, T3)
            6. Position size recommendation (% of capital)
            7. Risk assessment (LOW/MEDIUM/HIGH)
            8. Confidence level (0-100%)
            9. Key reasons for this recommendation

            RESPOND IN JSON FORMAT ONLY.
            """

            agent_result = await self._query_agent(user_id, session_id, combined_prompt)

            # Step 4: Combine all signals into final recommendation
            final_signal = self._generate_final_signal(
                engine_b_signal=engine_b_signal,
                market_pulse=market_pulse,
                agent_analysis=agent_result.get("response", ""),
                symbol=symbol
            )

            # Log the signal
            if self.db:
                self.db.collection("realtime_signals").add({
                    "user_id": user_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "final_signal": final_signal,
                    "engine_b_signal": engine_b_signal,
                    "market_pulse_summary": {
                        "nifty_change": market_pulse.get('indices', {}).get('nifty', {}).get('change_percent'),
                        "overall_signal": market_pulse.get('overall_signal')
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })

            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": final_signal,
                "components": {
                    "engine_b": engine_b_signal,
                    "market_pulse": {
                        "status": market_pulse.get('market_status', {}).get('status'),
                        "nifty": market_pulse.get('indices', {}).get('nifty', {}).get('change_percent'),
                        "overall": market_pulse.get('overall_signal')
                    },
                    "agent_analysis": agent_result.get("response", "")[:500]
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting realtime trade signal: {e}")
            return {"success": False, "error": str(e)}

    async def should_execute_trade(
        self,
        user_id: str,
        symbol: str,
        signal: Dict[str, Any],
        user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Final decision gate: Should we execute this trade?
        Combines AI recommendation with user's risk parameters.
        """
        try:
            min_confidence = user_config.get("min_confidence", 0.7)
            max_risk = user_config.get("max_risk_per_trade", 0.02)

            signal_confidence = signal.get("confidence", 0) / 100
            signal_action = signal.get("action", "WAIT")
            signal_risk = signal.get("risk_level", "HIGH")

            # Decision logic
            should_execute = False
            reason = ""

            if signal_action in ["WAIT", "HOLD"]:
                reason = "Signal recommends waiting"
            elif signal_confidence < min_confidence:
                reason = f"Confidence {signal_confidence:.0%} below threshold {min_confidence:.0%}"
            elif signal_risk == "HIGH" and max_risk < 0.03:
                reason = "Risk level too high for user's risk tolerance"
            elif signal_action in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
                should_execute = True
                reason = f"All conditions met: {signal_action} with {signal_confidence:.0%} confidence"

            return {
                "should_execute": should_execute,
                "action": signal_action if should_execute else "SKIP",
                "reason": reason,
                "signal_confidence": signal_confidence,
                "user_min_confidence": min_confidence,
                "risk_level": signal_risk,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in trade execution decision: {e}")
            return {"should_execute": False, "action": "SKIP", "reason": str(e)}

    # =========================================================================
    # Agent Query Methods
    # =========================================================================

    async def _query_agent(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Query the Financial Advisor Agent"""
        try:
            token = await self._get_access_token()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.stream_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "class_method": "async_stream_query",
                        "input": {
                            "message": message,
                            "user_id": user_id,
                            "session_id": session_id
                        }
                    }
                )

                if response.status_code == 200:
                    # Parse streaming response
                    response_text = response.text

                    # Extract the actual content from the response
                    try:
                        data = json.loads(response_text)
                        content = data.get("content", {}).get("parts", [{}])[0].get("text", "")
                        model = data.get("model_version", "gemini-2.5-pro")

                        # Update query count
                        if self.db:
                            self.db.collection("agent_sessions").document(user_id).update({
                                "last_query": datetime.utcnow().isoformat(),
                                "query_count": firestore.Increment(1)
                            })

                        return {
                            "success": True,
                            "response": content,
                            "model": model,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    except json.JSONDecodeError:
                        return {"success": True, "response": response_text, "model": "unknown"}
                else:
                    logger.error(f"Agent query failed: {response.text}")
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error querying agent: {e}")
            return {"success": False, "error": str(e)}

    async def chat_with_agent(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Free-form chat with Financial Advisor Agent.
        Use for general financial questions from frontend.
        """
        try:
            session_id = await self.get_user_session(user_id)
            if not session_id:
                return {"success": False, "error": "Could not get agent session"}

            # Add context if provided
            if context:
                message = f"""
                User Context:
                - Portfolio Value: {context.get('portfolio_value', 'N/A')}
                - Active Positions: {context.get('active_positions', 'N/A')}
                - Risk Profile: {context.get('risk_profile', 'moderate')}

                User Question: {message}
                """

            result = await self._query_agent(user_id, session_id, message)

            return {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "model": result.get("model", "gemini-2.5-pro"),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_analysis_prompt(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict = None,
        portfolio_context: Dict = None
    ) -> str:
        """Build comprehensive analysis prompt for the agent"""
        prompt = f"""
        TRADE OPPORTUNITY ANALYSIS for {symbol}

        Current Price: ₹{current_price}
        """

        if market_data:
            prompt += f"""
        Market Data:
        - 52 Week High: {market_data.get('week_52_high', 'N/A')}
        - 52 Week Low: {market_data.get('week_52_low', 'N/A')}
        - Volume: {market_data.get('volume', 'N/A')}
        - Average Volume: {market_data.get('avg_volume', 'N/A')}
        - P/E Ratio: {market_data.get('pe_ratio', 'N/A')}
        """

        if portfolio_context:
            prompt += f"""
        Portfolio Context:
        - Available Capital: ₹{portfolio_context.get('available_capital', 'N/A')}
        - Current Exposure to {symbol}: {portfolio_context.get('current_exposure', '0%')}
        - Risk Tolerance: {portfolio_context.get('risk_tolerance', 'moderate')}
        """

        prompt += """

        Please analyze this opportunity and provide:
        1. Overall assessment (BULLISH/BEARISH/NEUTRAL)
        2. Recommended action (BUY/SELL/HOLD/WAIT)
        3. Entry strategy
        4. Exit strategy (targets and stop loss)
        5. Position sizing recommendation
        6. Key risks to monitor
        7. Confidence level (0-100%)
        """

        return prompt

    def _parse_trade_recommendation(self, response: str) -> Dict[str, Any]:
        """Parse agent response into structured recommendation"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass

        # Default parsing based on keywords
        recommendation = {
            "action": TradeAction.HOLD.value,
            "confidence": 50,
            "risk_level": "MEDIUM",
            "entry_price": None,
            "stop_loss": None,
            "targets": [],
            "position_size_pct": 2,
            "reasoning": response[:500] if response else "No analysis available"
        }

        # Simple keyword extraction
        response_lower = response.lower() if response else ""

        if "strong buy" in response_lower or "strongly recommend buying" in response_lower:
            recommendation["action"] = TradeAction.STRONG_BUY.value
            recommendation["confidence"] = 85
        elif "buy" in response_lower and "don't buy" not in response_lower:
            recommendation["action"] = TradeAction.BUY.value
            recommendation["confidence"] = 70
        elif "strong sell" in response_lower:
            recommendation["action"] = TradeAction.STRONG_SELL.value
            recommendation["confidence"] = 85
        elif "sell" in response_lower and "don't sell" not in response_lower:
            recommendation["action"] = TradeAction.SELL.value
            recommendation["confidence"] = 70
        elif "wait" in response_lower or "hold off" in response_lower:
            recommendation["action"] = TradeAction.WAIT.value
            recommendation["confidence"] = 60

        if "high risk" in response_lower:
            recommendation["risk_level"] = "HIGH"
        elif "low risk" in response_lower:
            recommendation["risk_level"] = "LOW"

        return recommendation

    def _generate_final_signal(
        self,
        engine_b_signal: Dict,
        market_pulse: Dict,
        agent_analysis: str,
        symbol: str
    ) -> Dict[str, Any]:
        """Generate final trading signal combining all sources"""

        # Parse agent recommendation
        agent_rec = self._parse_trade_recommendation(agent_analysis)

        # Engine B signal
        eb_signal = engine_b_signal.get("signal", "HOLD")
        eb_confidence = engine_b_signal.get("confidence", 50)

        # Market conditions
        market_signal = market_pulse.get("overall_signal", "NEUTRAL")

        # Weighted scoring
        signals = {
            "STRONG_BUY": 2, "BUY": 1, "HOLD": 0, "NEUTRAL": 0,
            "SELL": -1, "STRONG_SELL": -2, "WAIT": 0, "BULLISH": 1, "BEARISH": -1
        }

        eb_score = signals.get(eb_signal.upper(), 0) * (eb_confidence / 100)
        market_score = signals.get(market_signal.upper(), 0) * 0.5
        agent_score = signals.get(agent_rec.get("action", "HOLD"), 0) * (agent_rec.get("confidence", 50) / 100)

        # Weighted average (Engine B: 40%, Agent: 40%, Market: 20%)
        final_score = (eb_score * 0.4) + (agent_score * 0.4) + (market_score * 0.2)

        # Determine action
        if final_score >= 1.2:
            action = TradeAction.STRONG_BUY.value
        elif final_score >= 0.6:
            action = TradeAction.BUY.value
        elif final_score <= -1.2:
            action = TradeAction.STRONG_SELL.value
        elif final_score <= -0.6:
            action = TradeAction.SELL.value
        elif abs(final_score) < 0.3:
            action = TradeAction.WAIT.value
        else:
            action = TradeAction.HOLD.value

        # Calculate combined confidence
        confidence = int(min(100, max(0, (
            eb_confidence * 0.4 +
            agent_rec.get("confidence", 50) * 0.4 +
            70 * 0.2  # Base market confidence
        ))))

        return {
            "action": action,
            "confidence": confidence,
            "score": round(final_score, 2),
            "risk_level": agent_rec.get("risk_level", "MEDIUM"),
            "entry_price": agent_rec.get("entry_price"),
            "stop_loss": agent_rec.get("stop_loss"),
            "targets": agent_rec.get("targets", []),
            "position_size_pct": agent_rec.get("position_size_pct", 2),
            "reasoning": {
                "engine_b": f"{eb_signal} ({eb_confidence}%)",
                "market": market_signal,
                "agent": agent_rec.get("action", "N/A")
            }
        }

    async def _get_engine_b_signal(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get trading signal from Engine B"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.engine_b_url}/api/v1/signal",
                    json={"symbol": symbol, "timeframe": timeframe}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"signal": "HOLD", "confidence": 50, "error": "Engine B unavailable"}
        except Exception as e:
            logger.error(f"Error getting Engine B signal: {e}")
            return {"signal": "HOLD", "confidence": 50, "error": str(e)}

    async def _get_market_pulse(self) -> Dict[str, Any]:
        """Get market pulse from Engine B"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.engine_b_url}/api/v1/market/pulse")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"overall_signal": "NEUTRAL", "market_status": {"status": "UNKNOWN"}}
        except Exception as e:
            logger.error(f"Error getting market pulse: {e}")
            return {"overall_signal": "NEUTRAL", "market_status": {"status": "UNKNOWN"}}


# =========================================================================
# Automated Trading Executor
# =========================================================================

class AutomatedTradeExecutor:
    """
    Executes trades automatically based on AI Agent recommendations.
    Integrates with the existing trading infrastructure.
    """

    def __init__(self, agent_integration: VertexAgentIntegration, firestore_db=None):
        self.agent = agent_integration
        self.db = firestore_db
        self.engine_c_url = "https://engine-c.infinityai.pro"

    def initialize(self, firestore_db):
        self.db = firestore_db
        self.agent.initialize(firestore_db)

    async def run_automated_trading_cycle(
        self,
        user_id: str,
        watchlist: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a complete automated trading cycle.
        Called by Cloud Scheduler or manually triggered.
        """
        results = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols_analyzed": 0,
            "signals_generated": 0,
            "trades_executed": 0,
            "trades_skipped": 0,
            "errors": [],
            "details": []
        }

        try:
            for symbol in watchlist:
                try:
                    # Step 1: Get real-time signal
                    signal_result = await self.agent.get_realtime_trade_signal(
                        user_id=user_id,
                        symbol=symbol,
                        timeframe="intraday"
                    )

                    results["symbols_analyzed"] += 1

                    if not signal_result.get("success"):
                        results["errors"].append(f"{symbol}: {signal_result.get('error')}")
                        continue

                    signal = signal_result.get("signal", {})
                    results["signals_generated"] += 1

                    # Step 2: Check if we should execute
                    decision = await self.agent.should_execute_trade(
                        user_id=user_id,
                        symbol=symbol,
                        signal=signal,
                        user_config=config
                    )

                    # Step 3: Execute or skip
                    if decision.get("should_execute"):
                        # Execute the trade
                        trade_result = await self._execute_trade(
                            user_id=user_id,
                            symbol=symbol,
                            signal=signal,
                            config=config
                        )

                        if trade_result.get("success"):
                            results["trades_executed"] += 1
                        else:
                            results["errors"].append(f"{symbol}: Trade execution failed - {trade_result.get('error')}")
                            results["trades_skipped"] += 1

                        results["details"].append({
                            "symbol": symbol,
                            "action": signal.get("action"),
                            "confidence": signal.get("confidence"),
                            "executed": trade_result.get("success", False),
                            "order_id": trade_result.get("order_id")
                        })
                    else:
                        results["trades_skipped"] += 1
                        results["details"].append({
                            "symbol": symbol,
                            "action": "SKIPPED",
                            "reason": decision.get("reason"),
                            "confidence": signal.get("confidence")
                        })

                except Exception as e:
                    results["errors"].append(f"{symbol}: {str(e)}")

            # Log the cycle results
            if self.db:
                self.db.collection("trading_cycles").add(results)

            return results

        except Exception as e:
            results["errors"].append(f"Cycle error: {str(e)}")
            return results

    async def _execute_trade(
        self,
        user_id: str,
        symbol: str,
        signal: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a trade via Engine C's Dhan integration"""
        try:
            action = signal.get("action", "").upper()

            if action not in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
                return {"success": False, "error": f"Invalid action: {action}"}

            transaction_type = "BUY" if "BUY" in action else "SELL"

            # Calculate quantity based on position size and trading amount
            trading_amount = config.get("trading_amount", 1000)
            entry_price = signal.get("entry_price") or signal.get("current_price", 100)
            quantity = max(1, int(trading_amount / entry_price))

            # Place order via internal API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.engine_c_url}/api/dhan/place-order",
                    json={
                        "user_id": user_id,
                        "symbol": symbol,
                        "transaction_type": transaction_type,
                        "quantity": quantity,
                        "order_type": "MARKET",
                        "product_type": "INTRADAY",
                        "price": 0,  # Market order
                        "trigger_price": 0,
                        "disclosed_quantity": 0,
                        "validity": "DAY",
                        "amo_time": "",
                        "bo_profit_value": 0,
                        "bo_stop_loss_value": float(signal.get("stop_loss", 0)) if signal.get("stop_loss") else 0
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": result.get("status") == "success",
                        "order_id": result.get("data", {}).get("orderId"),
                        "message": result.get("message", "Order placed")
                    }
                else:
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {"success": False, "error": str(e)}


# =========================================================================
# Global Instances
# =========================================================================

_vertex_agent = None
_trade_executor = None

def get_vertex_agent_integration() -> VertexAgentIntegration:
    """Get or create global VertexAgentIntegration instance"""
    global _vertex_agent
    if _vertex_agent is None:
        _vertex_agent = VertexAgentIntegration()
    return _vertex_agent

def get_automated_trade_executor() -> AutomatedTradeExecutor:
    """Get or create global AutomatedTradeExecutor instance"""
    global _trade_executor, _vertex_agent
    if _trade_executor is None:
        if _vertex_agent is None:
            _vertex_agent = VertexAgentIntegration()
        _trade_executor = AutomatedTradeExecutor(_vertex_agent)
    return _trade_executor
