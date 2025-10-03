from fastapi import APIRouter

router = APIRouter()

class BreakoutStrategy:
    async def evaluate_async(self, data):
        price = data.get("price", 0)
        resistance = data.get("resistance", 0)
        support = data.get("support", 0)

        if price > resistance:
            return {"action": "BUY", "symbol": data.get("symbol"), "reason": "Break above resistance"}
        elif price < support:
            return {"action": "SELL", "symbol": data.get("symbol"), "reason": "Break below support"}
        else:
            return {"action": "HOLD", "symbol": data.get("symbol"), "reason": "No breakout"}

@router.post("/evaluate")
async def evaluate_breakout(data: dict):
    strategy = BreakoutStrategy()
    return await strategy.evaluate_async(data)

@router.post("/strategy")
async def get_options_strategy(signal: str):
    from services.ai_models import generate_options_strategy
    strategy = generate_options_strategy(signal)
    return {"signal": signal, "options_strategy": strategy}
