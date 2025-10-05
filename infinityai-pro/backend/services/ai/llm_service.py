"""LLM service"""
class LLMService:
    async def generate_response(self, prompt):
        return {"response": f"Generated response for: {prompt}"}