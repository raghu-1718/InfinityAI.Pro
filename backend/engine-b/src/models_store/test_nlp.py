import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

print("=== 1. Test NLTK VADER Sentiment Analysis ===")
sia = SentimentIntensityAnalyzer()
text = "RBI keeps repo rate unchanged at 6.5%, signals bullish economic growth and healthy corporate earnings."
vader_res = sia.polarity_scores(text)
print("VADER Score:", vader_res)

print("\n=== 2. Test Hugging Face FinBERT Financial NLP ===")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
pipe = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
finbert_res = pipe(text)
print("FinBERT Result:", finbert_res)

print("\n=== 3. PyTorch CPU Performance ===")
print("PyTorch Version:", torch.__version__, "| Device:", "CPU" if not torch.cuda.is_available() else "CUDA")
