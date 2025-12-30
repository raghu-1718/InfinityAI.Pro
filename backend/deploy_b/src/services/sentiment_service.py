import logging
from typing import List, Dict

logger = logging.getLogger("sentiment_service")

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    _TRANSFORMERS_AVAILABLE = False


# ---- Singleton cache (important) ----
_TOKENIZER = None
_MODEL = None


class SentimentService:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled and _TRANSFORMERS_AVAILABLE
        self.device = "cpu"

        global _TOKENIZER, _MODEL

        if self.enabled and (_TOKENIZER is None or _MODEL is None):
            try:
                _TOKENIZER = AutoTokenizer.from_pretrained("ProsusAI/finbert")
                _MODEL = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
                _MODEL.eval()
                logger.info("✅ FinBERT sentiment loaded (singleton)")
            except Exception as e:
                logger.warning(f"FinBERT load failed: {e}; using rule-based fallback")
                self.enabled = False

        self.tokenizer = _TOKENIZER
        self.model = _MODEL

    def score_news(self, articles: List[Dict]) -> float:
        if not articles:
            return 0.0

        articles = articles[:10]  # hard cap for safety

        if self.enabled and self.model and self.tokenizer:
            try:
                texts = [
                    (a.get("title", "") + " " + a.get("description", ""))[:256]
                    for a in articles
                ]

                with torch.no_grad():
                    enc = self.tokenizer(
                        texts,
                        padding=True,
                        truncation=True,
                        return_tensors="pt"
                    )
                    logits = self.model(**enc).logits
                    probs = torch.softmax(logits, dim=-1).cpu().numpy()

                pos = probs[:, 2].mean()
                neg = probs[:, 0].mean()
                return float(pos - neg)

            except Exception as e:
                logger.warning(f"Transformer sentiment error: {e}")

        # ---- Rule-based fallback ----
        POS = {"beat", "surge", "rally", "profit", "upgrade", "growth", "gain", "record"}
        NEG = {"miss", "fall", "loss", "downgrade", "fraud", "raid", "ban", "default"}

        score = 0
        for a in articles:
            t = (a.get("title", "") + " " + a.get("description", "")).lower()
            score += sum(w in t for w in POS)
            score -= sum(w in t for w in NEG)

        return max(-1.0, min(1.0, score / 10.0))
