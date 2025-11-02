import aiohttp
import os

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv("VERTEX_AI_API_KEY", "")
        self.model = "gemini-2.5-flash-lite"
        self.url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{self.model}:generateContent"

    async def generate(self, text: str):
        payload = {
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200}
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.url}?key={self.api_key}", json=payload) as resp:
                return await resp.json()
