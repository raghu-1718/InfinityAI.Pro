"""
Firestore ai_signals_ledger Reference Adapter
"""
import os
import pandas as pd
from typing import Optional

class FirestoreLedgerAdapter:
    """
    Loads verified historical signals from scratch/cleaned_signals_ledger.csv or Firestore.
    """
    def __init__(self, csv_path: Optional[str] = None):
        if not csv_path:
            candidate_paths = [
                os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "brain", "89c9565c-fc5a-4258-9eae-cee0c517eb0a", "scratch", "cleaned_signals_ledger.csv"),
                "C:/Users/Raghu/Projects/InfinityAI.Pro/scratch/cleaned_signals_ledger.csv"
            ]
            for p in candidate_paths:
                if os.path.exists(p):
                    csv_path = p
                    break
        self.csv_path = csv_path

    def load_ledger(self) -> pd.DataFrame:
        if self.csv_path and os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            return df
        return pd.DataFrame()
