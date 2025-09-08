import asyncio
from app.market_data_handler import market_stream
from app.strategy_service import evaluate
from app.trade_execution import execute
from shared.utils.logger import get_logger

log = get_logger("engine")

async def engine_loop(user_id: str, stream_uri: str):
    async for tick in market_stream(stream_uri):
        decision = await evaluate(tick, user_id)
        if decision.get("action") in ("BUY", "SELL"):
            res = await execute(decision, user_id)
            log.info(f"Executed: {res}")

if __name__ == "__main__":
    # For multi-user, launch multiple tasks
    # Example single-user boot
    user_id = "YOUR_USER_ID"  # set via env or CLI if you like
    stream_uri = "wss://your-marketdata-feed"  # replace with your provider
    asyncio.run(engine_loop(user_id, stream_uri))
