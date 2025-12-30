import aiohttp
import os

class HuggingFaceProvider:
    def __init__(self):
        self.token = os.getenv("HUGGINGFACE_API_TOKEN", "")
        self.model = "distilbert-base-uncased"
        self.url = f"https://api-inference.huggingface.co/models/{self.model}"

    async def analyze_sentiment(self, text: str):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"inputs": text}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, json=payload) as resp:
                return await resp.json()
