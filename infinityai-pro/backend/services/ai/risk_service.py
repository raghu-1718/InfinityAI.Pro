# services/ai/risk_service.py
"""
InfinityAI.Pro - Multi-Cloud Risk Assessment Service
Supports Custom Python models (primary), AWS Fraud Detector (secondary), Azure Responsible AI Toolkit (tertiary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import numpy as np
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class RiskService:
    """Multi-cloud risk assessment service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize multi-cloud risk connections"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            self.initialized = True
            logger.info("✅ Multi-cloud Risk Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Risk service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Custom Python Models (Primary)
    async def custom_assess(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Custom risk assessment using Python models"""
        try:
            # Extract trade parameters
            symbol = trade_data.get('symbol', '')
            action = trade_data.get('action', 'BUY')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0.0)
            portfolio_value = trade_data.get('portfolio_value', 100000)

            # Position sizing check
            position_size_pct = (quantity * price) / portfolio_value
            max_position_size = kwargs.get('max_position_size', 0.05)  # 5% max

            # Risk metrics
            risk_score = 0.0
            risk_factors = []

            # Position size risk
            if position_size_pct > max_position_size:
                risk_score += 0.3
                risk_factors.append(f"Position size {position_size_pct:.1%} exceeds limit {max_position_size:.1%}")

            # Volatility risk (simplified)
            volatility = trade_data.get('volatility', 0.2)
            if volatility > 0.3:
                risk_score += 0.2
                risk_factors.append(f"High volatility: {volatility:.1%}")

            # Concentration risk
            existing_positions = trade_data.get('existing_positions', [])
            symbol_count = sum(1 for pos in existing_positions if pos.get('symbol') == symbol)
            if symbol_count > 2:
                risk_score += 0.1
                risk_factors.append(f"Multiple positions in {symbol} ({symbol_count})")

            # Stop loss check
            stop_loss_pct = trade_data.get('stop_loss_pct', 0.02)
            if stop_loss_pct > 0.05:  # Too wide stop loss
                risk_score += 0.1
                risk_factors.append(f"Wide stop loss: {stop_loss_pct:.1%}")

            # Determine risk level
            if risk_score < 0.2:
                risk_level = "low"
                approved = True
            elif risk_score < 0.4:
                risk_level = "medium"
                approved = True
            else:
                risk_level = "high"
                approved = False

            return {
                "approved": approved,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "position_size_pct": position_size_pct,
                "risk_factors": risk_factors,
                "recommendations": self._generate_risk_recommendations(risk_factors),
                "provider": "custom",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Custom risk assessment error: {e}")
            raise

    # AWS Fraud Detector (Secondary)
    async def aws_assess(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """AWS Fraud Detector risk assessment"""
        try:
            import boto3
            fraud_detector = boto3.client(
                'frauddetector',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            # Prepare event for fraud detection
            event_variables = {
                "symbol": trade_data.get('symbol', 'UNKNOWN'),
                "action": trade_data.get('action', 'BUY'),
                "quantity": str(trade_data.get('quantity', 0)),
                "price": str(trade_data.get('price', 0.0)),
                "portfolio_value": str(trade_data.get('portfolio_value', 100000))
            }

            # Get prediction (assuming detector exists)
            try:
                response = fraud_detector.get_event_prediction(
                    detectorId=self.config.AWS_FRAUD_DETECTOR_ID,
                    detectorVersionId="1",
                    eventId=f"trade_{datetime.now().timestamp()}",
                    eventTypeName="trade_event",
                    eventTimestamp=datetime.now().isoformat(),
                    entities=[{
                        "entityType": "trader",
                        "entityId": "infinity_ai"
                    }],
                    eventVariables=event_variables
                )

                # Parse fraud prediction
                outcomes = response.get("ruleResults", [])
                fraud_score = 0.0

                for outcome in outcomes:
                    if "high_risk" in outcome.get("ruleId", "").lower():
                        fraud_score += 0.5
                    elif "medium_risk" in outcome.get("ruleId", "").lower():
                        fraud_score += 0.3

                risk_level = "high" if fraud_score > 0.5 else "medium" if fraud_score > 0.2 else "low"

                return {
                    "approved": fraud_score < 0.5,
                    "risk_level": risk_level,
                    "risk_score": fraud_score,
                    "fraud_indicators": outcomes,
                    "provider": "aws",
                    "timestamp": datetime.now().isoformat()
                }

            except fraud_detector.exceptions.ResourceNotFoundException:
                # Fallback if detector doesn't exist
                logger.warning("AWS Fraud Detector not configured, using basic assessment")
                return await self.custom_assess(trade_data, **kwargs)

        except Exception as e:
            logger.error(f"AWS Fraud Detector error: {e}")
            raise

    # Azure Responsible AI Toolkit (Tertiary)
    async def azure_assess(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Azure Responsible AI risk assessment"""
        try:
            # Azure doesn't have a direct fraud detector, so we'll use a simplified approach
            # In production, this would integrate with Azure's responsible AI services

            # Simulate responsible AI assessment
            risk_score = 0.0
            ethical_concerns = []

            # Check for high-frequency trading patterns
            trade_frequency = trade_data.get('trade_frequency', 0)
            if trade_frequency > 10:  # More than 10 trades per day
                risk_score += 0.2
                ethical_concerns.append("High-frequency trading detected")

            # Check position concentration
            concentration = trade_data.get('concentration_risk', 0.0)
            if concentration > 0.3:  # More than 30% in one asset
                risk_score += 0.3
                ethical_concerns.append("High concentration risk")

            # Check for market manipulation patterns
            price_impact = trade_data.get('price_impact', 0.0)
            if price_impact > 0.01:  # More than 1% price impact
                risk_score += 0.4
                ethical_concerns.append("Potential market impact concerns")

            risk_level = "high" if risk_score > 0.5 else "medium" if risk_score > 0.2 else "low"

            return {
                "approved": risk_score < 0.4,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "ethical_concerns": ethical_concerns,
                "responsible_ai_check": True,
                "provider": "azure",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Azure Responsible AI error: {e}")
            raise

    # Portfolio risk assessment
    async def assess_portfolio_risk(self, portfolio_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Assess overall portfolio risk"""
        try:
            positions = portfolio_data.get('positions', [])
            total_value = portfolio_data.get('total_value', 0)

            if not positions or total_value == 0:
                return {"error": "Invalid portfolio data"}

            # Calculate portfolio metrics
            total_risk = 0
            concentration_risk = 0
            diversification_score = 0

            # Position concentration
            for position in positions:
                position_value = position.get('value', 0)
                weight = position_value / total_value

                if weight > 0.2:  # More than 20% in one position
                    concentration_risk += weight

                # Add volatility contribution
                volatility = position.get('volatility', 0.2)
                total_risk += weight * volatility

            # Diversification score (inverse of concentration)
            diversification_score = 1 - min(concentration_risk, 1.0)

            # Overall portfolio risk
            portfolio_risk_level = "high" if total_risk > 0.3 else "medium" if total_risk > 0.15 else "low"

            return {
                "portfolio_risk_level": portfolio_risk_level,
                "total_risk": total_risk,
                "concentration_risk": concentration_risk,
                "diversification_score": diversification_score,
                "position_count": len(positions),
                "recommendations": self._generate_portfolio_recommendations(
                    concentration_risk, diversification_score
                ),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Portfolio risk assessment error: {e}")
            return {"error": str(e)}

    # Compliance checks
    async def check_compliance(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Check regulatory compliance"""
        try:
            compliance_issues = []
            compliance_score = 1.0  # Start with perfect score

            # Check position limits (simplified SEBI-like rules)
            position_value = trade_data.get('quantity', 0) * trade_data.get('price', 0)
            portfolio_value = trade_data.get('portfolio_value', 100000)

            # Individual stock limit (typically 10-15% for retail)
            if position_value / portfolio_value > 0.15:
                compliance_issues.append("Position exceeds 15% of portfolio value")
                compliance_score -= 0.3

            # Daily trade frequency limit
            daily_trades = trade_data.get('daily_trade_count', 0)
            if daily_trades > 50:  # Unrealistic for retail
                compliance_issues.append("Excessive daily trading frequency")
                compliance_score -= 0.4

            # Check for pattern day trading (simplified)
            if daily_trades > 3:
                compliance_issues.append("Potential pattern day trading")
                compliance_score -= 0.2

            return {
                "compliant": compliance_score > 0.7,
                "compliance_score": compliance_score,
                "issues": compliance_issues,
                "regulatory_checks": ["position_limits", "trade_frequency", "pattern_trading"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return {"error": str(e)}

    # Legacy methods for backward compatibility
    async def assess_risk(self, trade_data: Dict[str, Any], **kwargs) -> Dict:
        """Assess risk using router"""
        try:
            from .router import AIRouter
            # Note: Router doesn't have risk methods yet, so we'll use direct provider calls
            providers = ["custom", "aws", "azure"]

            for provider in providers:
                try:
                    method_name = f"{provider}_assess"
                    if hasattr(self, method_name):
                        method = getattr(self, method_name)
                        result = await method(trade_data, **kwargs)
                        return result
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue

            return {"error": "All risk providers failed"}

        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {"error": str(e)}

    def _generate_risk_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        for factor in risk_factors:
            if "position size" in factor.lower():
                recommendations.append("Reduce position size to stay within risk limits")
                recommendations.append("Consider dollar-cost averaging for large positions")
            elif "volatility" in factor.lower():
                recommendations.append("Use wider stop-loss for volatile assets")
                recommendations.append("Consider options strategies for volatility management")
            elif "concentration" in factor.lower():
                recommendations.append("Diversify across different sectors/assets")
                recommendations.append("Implement position size limits per asset")
            elif "stop loss" in factor.lower():
                recommendations.append("Tighten stop-loss levels for better risk control")
                recommendations.append("Use trailing stops for trending assets")

        if not recommendations:
            recommendations.append("Risk profile looks good - maintain current strategy")

        return recommendations

    def _generate_portfolio_recommendations(self, concentration_risk: float, diversification_score: float) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []

        if concentration_risk > 0.5:
            recommendations.append("High concentration risk - reduce exposure to largest positions")
        elif concentration_risk > 0.3:
            recommendations.append("Moderate concentration risk - consider adding more assets")

        if diversification_score < 0.3:
            recommendations.append("Poor diversification - add assets from different sectors")
        elif diversification_score < 0.6:
            recommendations.append("Moderate diversification - consider geographic diversification")

        if not recommendations:
            recommendations.append("Portfolio diversification looks balanced")

        return recommendations

    async def health_check(self) -> Dict:
        """Check risk service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            health_status = {
                "custom": True,  # Always available
                "aws": bool(self.config.AWS_ACCESS_KEY_ID),
                "azure": bool(self.config.AZURE_AI_ENDPOINT)
            }

            return {
                "status": "healthy" if any(health_status.values()) else "degraded",
                "providers": health_status,
                "multi_cloud": True
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }