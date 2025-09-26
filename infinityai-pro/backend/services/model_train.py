# model_train.py
import os, pickle
import pandas as pd
import numpy as np
from utils.config import CONFIG
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
try:
    import lightgbm as lgb
    USE_LGB = True
except Exception:
    from sklearn.ensemble import RandomForestClassifier
    USE_LGB = False

def featurize(df:pd.DataFrame):
    df = df.copy()
    df["ret1"] = df["close"].pct_change().bfill()
    df["SMA_5"] = df["close"].rolling(5).mean().bfill()
    df["SMA_20"] = df["close"].rolling(20).mean().bfill()
    df["EMA_12"] = df["close"].ewm(span=12).mean().bfill()
    df["EMA_26"] = df["close"].ewm(span=26).mean().bfill()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    delta = df["close"].diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = (-delta).clip(lower=0).rolling(14).mean()
    df["RSI"] = 100 - (100/(1 + (up/(down.replace(0, np.nan)+1e-9))))
    # ATR
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean().bfill()
    df["VWAP"] = (df["close"] * df["volume"]).cumsum() / (df["volume"].cumsum()+1e-9)
    df.fillna(0, inplace=True)
    return df

def build_dataset(symbols, data_path):
    X = []
    y = []
    for sym in symbols:
        file = os.path.join(data_path, f"{sym}.csv")
        if not os.path.exists(file): continue
        df = pd.read_csv(file, parse_dates=["datetime"]).sort_values("datetime")
        df = featurize(df)
        # label: next candle positive return?
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
        features = df[["MACD","RSI","SMA_5","SMA_20","ret1"]].iloc[:-1]
        targ = df["target"].iloc[:-1]
        X.append(features.values)
        y.append(targ.values)
    if len(X)==0:
        raise RuntimeError("No data found")
    X = np.vstack(X)
    y = np.concatenate(y)
    return X, y

def train_and_save(symbols, data_path, model_path):
    X, y = build_dataset(symbols, data_path)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2, random_state=42, stratify=y)
    if USE_LGB:
        ltrain = lgb.Dataset(X_train, label=y_train)
        params = {"objective":"binary", "metric":"auc", "verbosity": -1}
        bst = lgb.train(params, ltrain, num_boost_round=200)
        preds = bst.predict(X_test)
        auc = roc_auc_score(y_test, preds)
        print("LGB AUC:", auc)
        with open(model_path, "wb") as f:
            pickle.dump(bst, f)
    else:
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        preds = clf.predict_proba(X_test)[:,1]
        auc = roc_auc_score(y_test, preds)
        print("RF AUC:", auc)
        with open(model_path, "wb") as f:
            pickle.dump(clf, f)
    print("Model saved to", model_path)

if __name__ == "__main__":
    symbols = ["NIFTY","BANKNIFTY"]  # expand as data available
    data_path = CONFIG.BACKTEST_DATA_PATH
    os.makedirs(os.path.dirname(CONFIG.MODEL_PATH), exist_ok=True)
    train_and_save(symbols, data_path, CONFIG.MODEL_PATH)