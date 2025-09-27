# Azure AI Foundry Integration for InfinityAI.Pro

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

class AzureAIClient:
    """
    Azure AI Foundry client for managed AI services
    Provides access to GPT-4, DALL-E, Whisper, and other Azure AI models
    """

    def __init__(self, endpoint: str, key: str, project: str = None):
        self.endpoint = endpoint.rstrip('/')
        self.key = key
        self.project = project
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'api-key': self.key,
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, url: str, payload: Dict) -> Dict:
        """Make authenticated request to Azure AI"""
        if not self.session:
            async with aiohttp.ClientSession(
                headers={
                    'api-key': self.key,
                    'Content-Type': 'application/json'
                }
            ) as session:
                async with session.post(url, json=payload) as response:
                    return await response.json()
        else:
            async with self.session.post(url, json=payload) as response:
                return await response.json()

    async def chat_completion(self, message: str, model: str = "gpt-4",
                            temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        """
        Generate chat completion using Azure OpenAI GPT-4
        """
        try:
            url = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version=2023-12-01-preview"

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            response = await self._make_request(url, payload)

            if 'choices' in response and len(response['choices']) > 0:
                return {
                    "success": True,
                    "response": response['choices'][0]['message']['content'],
                    "usage": response.get('usage', {}),
                    "model": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "No response generated",
                    "details": response
                }

        except Exception as e:
            logger.error(f"Azure AI chat completion error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_image(self, prompt: str, size: str = "1024x1024",
                           quality: str = "standard", style: str = "vivid") -> Dict:
        """
        Generate image using Azure DALL-E 3
        """
        try:
            url = f"{self.endpoint}/openai/deployments/dall-e-3/images/generations?api-version=2023-12-01-preview"

            payload = {
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "style": style,
                "n": 1
            }

            response = await self._make_request(url, payload)

            if 'data' in response and len(response['data']) > 0:
                return {
                    "success": True,
                    "image_url": response['data'][0]['url'],
                    "revised_prompt": response['data'][0].get('revised_prompt', prompt),
                    "usage": response.get('usage', {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Image generation failed",
                    "details": response
                }

        except Exception as e:
            logger.error(f"Azure AI image generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> Dict:
        """
        Convert speech to text using Azure Whisper
        """
        try:
            url = f"{self.endpoint}/openai/deployments/whisper/audio/transcriptions?api-version=2023-12-01-preview"

            # For binary data, we need to use multipart/form-data
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename='audio.wav')
            data.add_field('model', 'whisper-1')
            data.add_field('language', language)

            if not self.session:
                async with aiohttp.ClientSession(
                    headers={'api-key': self.key}
                ) as session:
                    async with session.post(url, data=data) as response:
                        result = await response.json()
            else:
                async with self.session.post(url, data=data) as response:
                    result = await response.json()

            if 'text' in result:
                return {
                    "success": True,
                    "text": result['text'],
                    "language": result.get('language', language),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Speech-to-text failed",
                    "details": result
                }

        except Exception as e:
            logger.error(f"Azure AI speech-to-text error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> Dict:
        """
        Generate embeddings using Azure OpenAI
        """
        try:
            url = f"{self.endpoint}/openai/deployments/{model}/embeddings?api-version=2023-12-01-preview"

            payload = {
                "input": text,
                "model": model
            }

            response = await self._make_request(url, payload)

            if 'data' in response and len(response['data']) > 0:
                return {
                    "success": True,
                    "embedding": response['data'][0]['embedding'],
                    "usage": response.get('usage', {}),
                    "model": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Embedding generation failed",
                    "details": response
                }

        except Exception as e:
            logger.error(f"Azure AI embeddings error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def health_check(self) -> Dict:
        """Check Azure AI service health"""
        try:
            # Simple chat completion as health check
            test_response = await self.chat_completion(
                "Hello, this is a health check. Respond with 'OK' if you can read this.",
                max_tokens=10
            )

            return {
                "status": "healthy" if test_response.get("success") else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "details": test_response
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global Azure AI client instance
azure_ai_client = None

async def get_azure_ai_client() -> AzureAIClient:
    """Get or create Azure AI client instance"""
    global azure_ai_client

    if azure_ai_client is None:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_KEY")
        project = os.getenv("AZURE_AI_PROJECT")

        if not endpoint or not key:
            raise ValueError("Azure AI credentials not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")

        azure_ai_client = AzureAIClient(endpoint, key, project)

    return azure_ai_client