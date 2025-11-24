import logging, math
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger("sentiment_service")

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    _TRANSFORMERS_AVAILABLE = False

class SentimentService:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled and _TRANSFORMERS_AVAILABLE
        self.device = "cpu"
        if self.enabled:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
                self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
                self.model.eval()
                logger.info("FinBERT sentiment loaded")
            except Exception as e:
                logger.warning(f"FinBERT load failed: {e}; using rule-based fallback")
                self.enabled = False

    def score_news(self, articles: List[Dict]) -> float:
        if not articles:
            return 0.0
        if self.enabled:
            try:
                texts = [a.get("title","")[:256] for a in articles[:8]]
                import numpy as np, torch
                with torch.no_grad():
                    enc = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
                    logits = self.model(**enc).logits
                    probs = torch.softmax(logits, dim=-1).cpu().numpy()
                pos = probs[:,2].mean()
                neg = probs[:,0].mean()
                return float(pos - neg)
            except Exception as e:
                logger.warning(f"Transformer scoring error: {e}")
        POS = ["beat","surge","rally","profit","upgrade","growth","gain","record"]
        NEG = ["miss","fall","loss","downgrade","fraud","raid","ban","default"]
        score = 0
        for a in articles[:10]:
            t = (a.get("title","") + " " + a.get("description","")).lower()
            score += sum(1 for w in POS if w in t)
            score -= sum(1 for w in NEG if w in t)
        return max(-1.0, min(1.0, score/10.0))
