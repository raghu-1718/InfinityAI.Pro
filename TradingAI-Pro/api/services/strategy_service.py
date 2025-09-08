import asyncio
from typing import Any, Dict, List
from core.strategies.breakout import BreakoutStrategy
# from core.ai_model import get_ai_signal  # Example for AI model integration

strategies_registry = [BreakoutStrategy()]

async def evaluate_strategies(market_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
	decisions: List[Dict[str, Any]] = []
	for strategy in strategies_registry:
		# If strategy has async evaluate_async, use it; else fallback to sync
		if hasattr(strategy, 'evaluate_async'):
			decision = await strategy.evaluate_async(market_data)
		else:
			decision = strategy.evaluate(market_data)
		decisions.append(decision)
	# Optionally, get AI model signal and add to decisions
	# ai_decision = await get_ai_signal(market_data)
	# decisions.append(ai_decision)
	return aggregate_decisions(decisions)

def aggregate_decisions(decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
	# Simple aggregation: pick first actionable decision
	for d in decisions:
		if d['action'] in ['BUY', 'SELL']:
			return d
	return decisions[0] if decisions else {"action": "HOLD"}
