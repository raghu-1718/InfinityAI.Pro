# services/ai/vision_service.py
"""
InfinityAI.Pro - Multi-Cloud Vision Service
Supports RunPod YOLO (primary), Azure Vision (secondary), AWS Rekognition (tertiary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import base64
import io
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class VisionService:
    """Multi-cloud vision service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize multi-cloud vision connections"""
        try:
            self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for image processing
            self.initialized = True
            logger.info("✅ Multi-cloud Vision Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Vision service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Azure Vision (Primary)
    async def azure_analyze(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """Azure Computer Vision analysis"""
        try:
            azure_url = f"{self.config.AZURE_VISION_ENDPOINT}/computervision/imageanalysis:analyze?api-version=2023-02-01-preview&features=caption,tags,objects,denseCaptions"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_VISION_KEY,
                "Content-Type": "application/octet-stream"
            }

            params = {
                "language": kwargs.get("language", "en"),
                "model-version": "latest"
            }

            async with self.client.post(azure_url, data=image_data, headers=headers, params=params) as resp:
                resp.raise_for_status()
                result = resp.json()
                return result

        except Exception as e:
            logger.error(f"Azure Vision error: {e}")
            raise

    async def azure_detect(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """Azure object detection"""
        try:
            analysis = await self.azure_analyze(image_data, **kwargs)
            objects = analysis.get("objects", [])

            # Convert to consistent format
            detections = []
            for obj in objects:
                detection = {
                    "class_name": obj.get("object", ""),
                    "confidence": obj.get("confidence", 0.0),
                    "bbox": {
                        "x1": obj.get("rectangle", {}).get("x", 0),
                        "y1": obj.get("rectangle", {}).get("y", 0),
                        "x2": obj.get("rectangle", {}).get("x", 0) + obj.get("rectangle", {}).get("w", 0),
                        "y2": obj.get("rectangle", {}).get("y", 0) + obj.get("rectangle", {}).get("h", 0)
                    }
                }
                detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"Azure detection error: {e}")
            raise

    # AWS Rekognition (Secondary)
    async def aws_analyze(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """AWS Rekognition analysis"""
        try:
            import boto3
            rekognition = boto3.client(
                'rekognition',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            # Detect labels with detailed attributes
            labels_response = rekognition.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=20,
                MinConfidence=kwargs.get('min_confidence', 50.0)
            )
            labels = labels_response.get('Labels', [])

            # Detect text
            text_response = rekognition.detect_text(Image={'Bytes': image_data})
            text_detections = text_response.get('TextDetections', [])

            # Detect faces
            faces_response = rekognition.detect_faces(Image={'Bytes': image_data})
            faces = faces_response.get('FaceDetails', [])

            return {
                "labels": labels,
                "text_detections": text_detections,
                "faces": faces,
                "metadata": {
                    "label_count": len(labels),
                    "text_count": len(text_detections),
                    "face_count": len(faces)
                }
            }

        except Exception as e:
            logger.error(f"AWS Rekognition error: {e}")
            raise

    async def aws_detect(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """AWS object detection"""
        try:
            analysis = await self.aws_analyze(image_data, **kwargs)
            labels = analysis.get("labels", [])

            # Convert to consistent format
            detections = []
            for label in labels:
                detection = {
                    "class_name": label.get("Name", ""),
                    "confidence": label.get("Confidence", 0.0) / 100.0,  # Convert to 0-1 scale
                    "bbox": {},  # Rekognition doesn't provide bounding boxes for labels
                    "instances": label.get("Instances", [])
                }
                detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"AWS detection error: {e}")
            raise

    # Legacy methods for backward compatibility
    async def detect_objects(self, image_data: bytes, **kwargs) -> Dict:
        """Detect objects using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                detections = await router.detect_objects(image_data, **kwargs)

            return {
                "detections": detections,
                "total_objects": len(detections),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
            return {"error": str(e)}

    async def analyze_image(self, image_data: bytes, **kwargs) -> Dict:
        """Analyze image using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                analysis = await router.analyze_image(image_data, **kwargs)

            return {
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}

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
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict:
        """Check vision service health"""
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