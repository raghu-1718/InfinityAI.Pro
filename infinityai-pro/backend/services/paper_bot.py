# paper_bot.py
import asyncio, pickle, time, math
import pandas as pd
from utils.config import CONFIG
from datetime import datetime
from typing import Optional
from services.model_train import featurize
# BrokerAdapter and Fetcher are light-weight; replace with real implementations or D module

class DummyBroker:
    def __init__(self, paper=True):
        self.paper = paper
    async def place_order(self, symbol, side, qty, price=None, order_type="MARKET"):
        await asyncio.sleep(0.05)
        if self.paper:
            return {"ok":True, "order_id": f"PAPER_{int(time.time()*1000)}"}
        else:
            # Integrate real order call
            return {"ok":False, "error":"Real broker not configured"}

class DummyFetcher:
    async def get_candles(self, symbol, timeframe="5m", length=200):
        # reuse the backtest's CSV if present, else synthetic
        import os
        path = CONFIG.BACKTEST_DATA_PATH
        file = os.path.join(path, f"{symbol}.csv")
        if os.path.exists(file):
            df = pd.read_csv(file, parse_dates=["datetime"]).sort_values("datetime").iloc[-length:].reset_index(drop=True)
            df.set_index("datetime", inplace=True)
            return df
        # synthetic fallback
        now = datetime.now()
        dates = [now - pd.Timedelta(minutes=5*i) for i in range(length)][::-1]
        prices = 10000 + pd.Series(np.cumsum(np.random.randn(length)))
        df = pd.DataFrame({"datetime":dates,"open":prices,"high":prices+1,"low":prices-1,"close":prices,"volume":100})
        df.set_index("datetime", inplace=True)
        return df

class PaperBot:
    def __init__(self, config=CONFIG):
        self.cfg = config
        self.broker = DummyBroker(paper=config.PAPER_MODE)
        self.fetcher = DummyFetcher()
        self.equity = config.CAPITAL
        self.model = None
        # load model if exists
        try:
            with open(self.cfg.MODEL_PATH,"rb") as f:
                self.model = pickle.load(f)
                print("Loaded model from", self.cfg.MODEL_PATH)
        except Exception as e:
            print("No model loaded; proceeding without ML", e)

    def compute_features_row(self, df):
        df2 = featurize(df.reset_index())
        return df2

    async def run_once(self):
        for sym in self.cfg.SYMBOLS:
            df = await self.fetcher.get_candles(sym, "5m", 200)
            df_feat = self.compute_features_row(df)
            last = df_feat.iloc[-1]
            # simple rule + ml
            macd = last["MACD"]
            rsi = last["RSI"]
            price = last["close"]
            ml_prob = 0.5
            if self.model is not None:
                X = last[["MACD","RSI","SMA_5","SMA_20","ret1"]].values.reshape(1,-1)
                try:
                    if hasattr(self.model, "predict_proba"):
                        ml_prob = float(self.model.predict_proba(X)[:,1])
                    else:
                        ml_prob = float(self.model.predict(X))
                except Exception:
                    ml_prob = 0.5
            signal = "HOLD"
            if macd>0 and price>last["VWAP"] and 35<rsi<70 and ml_prob>0.6:
                signal="BUY"
            elif macd<0 and price<last["VWAP"] and 30<rsi<65 and ml_prob<0.4:
                signal="SELL"
            print(f"{sym} signal {signal} ml={ml_prob:.2f} macd={macd:.4f} rsi={rsi:.2f}")
            if signal!="HOLD":
                # simulate option premium fetch & decide qty
                premium = max(10.0, price*0.0006)
                # position sizing
                risk_amount = self.equity * self.cfg.RISK_PER_TRADE_PCT
                stop_loss_amount = premium * 0.6
                contracts = int(max(1, math.floor( risk_amount/(stop_loss_amount+1e-9) )))
                cost = contracts * premium
                if cost > self.equity*0.3:
                    contracts = int(math.floor((self.equity*0.3)/(premium+1e-9)))
                if contracts<=0:
                    print("Not enough capital for any contract")
                    continue
                # place order (paper)
                res = await self.broker.place_order(sym+"_OPT", "BUY", contracts)
                if res.get("ok"):
                    print("Paper executed", sym, contracts, "premium", premium)
                    # simple random outcome simulation
                    pnl = (np.random.choice([1,-1], p=[0.55,0.45]) * cost * np.random.uniform(0.2,1.5))
                    self.equity = self.equity - cost + cost + pnl
                    print("Sim pnl", pnl, "new equity", self.equity)
        return True

    async def run_day(self, cycles=6, interval_sec=60):
        for _ in range(cycles):
            await self.run_once()
            await asyncio.sleep(interval_sec)
        print("End equity:", self.equity)

if __name__ == "__main__":
    bot = PaperBot(CONFIG)
    asyncio.run(bot.run_day(cycles=6, interval_sec=2))