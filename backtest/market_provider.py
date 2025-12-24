import pandas as pd

class BacktestMarketProvider:
    def __init__(self, data_source):
        if isinstance(data_source, str):
            self.df = pd.read_csv(data_source, parse_dates=["timestamp"])
        else:
            self.df = data_source.copy()
            if "timestamp" in self.df.columns and not pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
                
        self.pointer = 0

    def has_next(self):
        return self.pointer < len(self.df)

    def next_tick(self):
        row = self.df.iloc[self.pointer]
        self.pointer += 1
        return row.to_dict()
