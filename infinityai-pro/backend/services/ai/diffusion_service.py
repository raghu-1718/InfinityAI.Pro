# services/ai/diffusion_service.py
"""
InfinityAI.Pro - Multi-Cloud Diffusion Service
Supports Azure OpenAI DALL-E (primary), AWS Titan Image Generator (secondary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import base64
import io
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DiffusionService:
    """Multi-cloud diffusion service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize multi-cloud diffusion connections"""
        try:
            self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for image generation
            self.initialized = True
            logger.info("✅ Multi-cloud Diffusion Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Diffusion service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Azure OpenAI DALL-E (Primary)
    async def azure_generate(self, prompt: str, **kwargs) -> bytes:
        """Azure OpenAI DALL-E image generation"""
        try:
            azure_url = f"{self.config.AZURE_OPENAI_ENDPOINT}/openai/deployments/dall-e-3/images/generations?api-version=2024-02-15-preview"
            headers = {
                "api-key": self.config.AZURE_OPENAI_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "prompt": prompt,
                "n": kwargs.get("n", 1),
                "size": kwargs.get("size", "1024x1024"),
                "quality": kwargs.get("quality", "standard"),
                "style": kwargs.get("style", "natural")
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            # Extract image URL and download
            image_url = result["data"][0]["url"]
            async with self.client.get(image_url) as img_resp:
                img_resp.raise_for_status()
                return img_resp.content

        except Exception as e:
            logger.error(f"Azure DALL-E error: {e}")
            raise

            payload = {
                "input": {
                    "prompt": prompt,
                    "negative_prompt": kwargs.get("negative_prompt", ""),
                    "steps": kwargs.get("steps", 20),
                    "guidance_scale": kwargs.get("guidance_scale", 7.5),
                    "width": kwargs.get("width", 512),
                    "height": kwargs.get("height", 512),
                    "model": kwargs.get("model", "stabilityai/stable-diffusion-2-1")
                }
            }

            async with self.client.post(runpod_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()
                # Decode base64 image
                image_b64 = result.get("output", {}).get("image", "")
                return base64.b64decode(image_b64)

        except Exception as e:
            logger.error(f"RunPod Stable Diffusion error: {e}")
            raise

    # Azure Custom Vision (Secondary) - Note: Limited image generation capabilities
    async def azure_generate(self, prompt: str, **kwargs) -> bytes:
        """Azure Custom Vision - Limited generation capabilities"""
        try:
            # Azure Custom Vision is more for classification/training than generation
            # This would be a placeholder for future Azure OpenAI DALL-E integration
            azure_url = f"{self.config.AZURE_OPENAI_ENDPOINT}/openai/images/generations:submit?api-version=2023-06-01-preview"
            headers = {
                "api-key": self.config.AZURE_OPENAI_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "prompt": prompt,
                "n": 1,
                "size": f"{kwargs.get('width', 512)}x{kwargs.get('height', 512)}"
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

                # Get the result URL and download the image
                image_url = result.get("data", [{}])[0].get("url", "")
                if image_url:
                    async with self.client.get(image_url) as img_resp:
                        return await img_resp.read()
                else:
                    raise Exception("No image URL in response")

        except Exception as e:
            logger.error(f"Azure image generation error: {e}")
            raise

    # AWS Titan Image Generator (Secondary)
    async def aws_generate(self, prompt: str, **kwargs) -> bytes:
        """AWS Titan Image Generator"""
        try:
            import boto3
            bedrock = boto3.client(
                'bedrock-runtime',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            payload = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": kwargs.get("negative_prompt", "")
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": kwargs.get("height", 1024),
                    "width": kwargs.get("width", 1024),
                    "cfgScale": kwargs.get("cfg_scale", 8.0),
                    "seed": kwargs.get("seed", 42)
                }
            }

            response = bedrock.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )

            result = json.loads(response["Body"].read())
            # Extract base64 image
            image_b64 = result.get("images", [""])[0]
            return base64.b64decode(image_b64)

        except Exception as e:
            logger.error(f"AWS Titan Image Generator error: {e}")
            raise

    # Legacy methods for backward compatibility
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        """Generate image using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                image_data = await router.generate_image(prompt, **kwargs)

            # Convert to base64 for response
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            return {
                "image_base64": image_base64,
                "prompt": prompt,
                "parameters": kwargs,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict:
        """Check diffusion service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            # Check all providers
            from .router import AIRouter
            async with AIRouter() as router:
                health_status = await router.get_health_status()

            return {
                "status": "healthy",
                "providers": health_status,
                "multi_cloud": True
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }