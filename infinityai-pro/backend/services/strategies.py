from api.options import BreakoutStrategy

strategies_registry = [BreakoutStrategy()]

async def evaluate_strategies(data, user_id):
    decisions = []
    for s in strategies_registry:
        d = await s.evaluate_async(data)
        decisions.append(d)
    for d in decisions:
        if d.get('action') != 'HOLD':
            return d
    return {"action": "HOLD", "reason": "No active signal"}