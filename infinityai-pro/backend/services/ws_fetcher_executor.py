# ws_fetcher_executor.py
import asyncio, json, time
import aiohttp
from typing import Callable, Any, Dict

class WSFetcher:
    def __init__(self, url:str, subscribe_payload:dict, message_callback:Callable[[dict],Any], reconnect_delay=2.0):
        self.url = url
        self.sub_payload = subscribe_payload
        self.cb = message_callback
        self.reconnect_delay = reconnect_delay
        self.keep_running = True
        self.session = None
        self.ws = None

    async def connect(self):
        while self.keep_running:
            try:
                async with aiohttp.ClientSession() as session:
                    self.session = session
                    async with session.ws_connect(self.url, heartbeat=30) as ws:
                        self.ws = ws
                        # send subscription
                        if self.sub_payload:
                            await ws.send_json(self.sub_payload)
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                # user callback handles ticks/candles
                                await self.cb(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            except Exception as e:
                print("WS error", e, "reconnecting in", self.reconnect_delay)
                await asyncio.sleep(self.reconnect_delay)

    def stop(self):
        self.keep_running = False

class OrderExecutor:
    def __init__(self, broker_adapter):
        self.broker = broker_adapter
        self.order_queue = asyncio.Queue()
        self.running = True

    async def submit_order(self, order:dict):
        await self.order_queue.put(order)

    async def worker(self):
        while self.running:
            try:
                order = await self.order_queue.get()
                # pre-trade checks: margin, exposure, risk
                # call broker adapter
                res = await self.broker.place_order(order["symbol"], order["side"], order["qty"], price=order.get("price"), order_type=order.get("order_type","MARKET"))
                print("Order executed res:", res)
                await asyncio.sleep(0.05)  # slight throttle
            except Exception as e:
                print("Order execution error", e)

    def stop(self):
        self.running = False

# USAGE example
async def tick_handler(msg):
    # parse incoming tick and convert to candle aggregator or event trigger
    print("Tick", msg)

class DummyBrokerAdapter:
    async def place_order(self, symbol, side, qty, price=None, order_type="MARKET"):
        await asyncio.sleep(0.05)
        return {"ok":True, "order_id": int(time.time()*1000)%100000}

async def main_ws():
    url = "wss://example-data-feed"  # change to broker-provided websocket
    sub = {"action":"subscribe","symbols":["NIFTY","BANKNIFTY"]}
    fetcher = WSFetcher(url, sub, tick_handler)
    bro = DummyBrokerAdapter()
    exe = OrderExecutor(bro)
    # run both coroutines
    await asyncio.gather(fetcher.connect(), exe.worker())

if __name__ == "__main__":
    try:
        asyncio.run(main_ws())
    except KeyboardInterrupt:
        print("Stopped")