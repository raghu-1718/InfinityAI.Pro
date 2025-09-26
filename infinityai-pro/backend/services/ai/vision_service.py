# services/ai/vision_service.py
"""
InfinityAI.Pro - Vision Service
YOLOv8 for object detection + Stable Diffusion for image generation
"""

import os
import tempfile
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class VisionService:
    """Vision service combining object detection and image generation"""

    def __init__(self, yolo_config: Dict, diffusers_config: Dict):
        self.yolo_config = yolo_config
        self.diffusers_config = diffusers_config
        self.yolo_model = None
        self.diffusers_pipe = None
        self.initialized = False

    async def initialize(self):
        """Initialize YOLO and Diffusers models"""
        try:
            # Initialize YOLO
            logger.info(f"Loading YOLO model: {self.yolo_config['model']}")
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.yolo_config['model'])

            # Initialize Stable Diffusion (optional - can be heavy)
            try:
                import psutil
                disk = psutil.disk_usage('/')
                free_gb = disk.free / (1024**3)
                
                if free_gb < 5:  # Need at least 5GB free for SD model
                    logger.warning(f"Insufficient disk space for Stable Diffusion ({free_gb:.1f}GB free). Skipping SD initialization.")
                    self.diffusers_pipe = None
                else:
                    logger.info(f"Loading Stable Diffusion model: {self.diffusers_config['model']}")
                    from diffusers import StableDiffusionPipeline
                    import torch

                    self.diffusers_pipe = StableDiffusionPipeline.from_pretrained(
                        self.diffusers_config['model'],
                        torch_dtype=torch.float16 if self.diffusers_config['device'] == 'cuda' else torch.float32
                    )

                    if self.diffusers_config['device'] == 'cuda':
                        self.diffusers_pipe = self.diffusers_pipe.to("cuda")

                    logger.info("✅ Vision Service initialized with YOLO and Stable Diffusion")

            except ImportError:
                logger.warning("psutil not available, proceeding with SD initialization")
                # Fallback to original code
                logger.info(f"Loading Stable Diffusion model: {self.diffusers_config['model']}")
                from diffusers import StableDiffusionPipeline
                import torch

                self.diffusers_pipe = StableDiffusionPipeline.from_pretrained(
                    self.diffusers_config['model'],
                    torch_dtype=torch.float16 if self.diffusers_config['device'] == 'cuda' else torch.float32
                )

                if self.diffusers_config['device'] == 'cuda':
                    self.diffusers_pipe = self.diffusers_pipe.to("cuda")

                logger.info("✅ Vision Service initialized with YOLO and Stable Diffusion")

            except Exception as e:
                logger.warning(f"Stable Diffusion not available: {e}")
                logger.info("✅ Vision Service initialized with YOLO only")

            self.initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Vision service: {e}")
            raise

    async def close(self):
        """Close vision service"""
        # Models don't need explicit closing
        pass

    async def detect_objects(self, image_data: bytes, filename: str = None) -> Dict:
        """Detect objects in image using YOLO"""
        try:
            if not self.initialized or not self.yolo_model:
                raise RuntimeError("Vision service not initialized")

            # Save image data to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".jpg" if filename and filename.endswith('.jpg') else ".png",
                delete=False
            ) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name

            try:
                # Run YOLO detection
                results = self.yolo_model(temp_path, conf=self.yolo_config['conf_threshold'])

                # Process results
                detections = []
                for result in results:
                    for box in result.boxes:
                        detection = {
                            "class_id": int(box.cls.cpu().numpy()[0]),
                            "class_name": result.names[int(box.cls.cpu().numpy()[0])],
                            "confidence": float(box.conf.cpu().numpy()[0]),
                            "bbox": {
                                "x1": float(box.xyxy.cpu().numpy()[0][0]),
                                "y1": float(box.xyxy.cpu().numpy()[0][1]),
                                "x2": float(box.xyxy.cpu().numpy()[0][2]),
                                "y2": float(box.xyxy.cpu().numpy()[0][3])
                            },
                            "area": float((box.xyxy.cpu().numpy()[0][2] - box.xyxy.cpu().numpy()[0][0]) *
                                        (box.xyxy.cpu().numpy()[0][3] - box.xyxy.cpu().numpy()[0][1]))
                        }
                        detections.append(detection)

                # Sort by confidence
                detections.sort(key=lambda x: x['confidence'], reverse=True)

                return {
                    "detections": detections,
                    "total_objects": len(detections),
                    "image_info": {
                        "width": results[0].orig_shape[1] if results else 0,
                        "height": results[0].orig_shape[0] if results else 0
                    },
                    "timestamp": self._get_timestamp()
                }

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return {"error": str(e)}

    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        """Generate image from text prompt using Stable Diffusion"""
        try:
            if not self.initialized or not self.diffusers_pipe:
                raise RuntimeError("Stable Diffusion not available")

            # Generate image
            logger.info(f"Generating image for prompt: {prompt[:50]}...")

            result = self.diffusers_pipe(
                prompt,
                num_inference_steps=kwargs.get('steps', 20),
                guidance_scale=kwargs.get('guidance_scale', 7.5),
                height=kwargs.get('height', 512),
                width=kwargs.get('width', 512)
            )

            # Convert to base64
            image = result.images[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            return {
                "image_base64": image_base64,
                "prompt": prompt,
                "parameters": {
                    "steps": kwargs.get('steps', 20),
                    "guidance_scale": kwargs.get('guidance_scale', 7.5),
                    "height": kwargs.get('height', 512),
                    "width": kwargs.get('width', 512)
                },
                "model": self.diffusers_config['model'],
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {"error": str(e)}

    async def analyze_image(self, image_data: bytes, analysis_type: str = "general") -> Dict:
        """Comprehensive image analysis"""
        try:
            # First detect objects
            detection_result = await self.detect_objects(image_data)

            if "error" in detection_result:
                return detection_result

            # Analyze based on type
            analysis = {
                "detection": detection_result,
                "analysis_type": analysis_type,
                "insights": []
            }

            if analysis_type == "trading_chart":
                analysis["insights"] = self._analyze_trading_chart(detection_result)
            elif analysis_type == "market_news":
                analysis["insights"] = self._analyze_market_news(detection_result)
            else:
                analysis["insights"] = self._general_image_insights(detection_result)

            analysis["timestamp"] = self._get_timestamp()
            return analysis

        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return {"error": str(e)}

    def _analyze_trading_chart(self, detection_result: Dict) -> List[str]:
        """Analyze trading chart patterns"""
        insights = []
        detections = detection_result.get("detections", [])

        # Look for chart elements
        has_lines = any(d["class_name"].lower() in ["line", "trendline"] for d in detections)
        has_candles = any(d["class_name"].lower() in ["candle", "candlestick"] for d in detections)
        has_indicators = any(d["class_name"].lower() in ["indicator", "oscillator"] for d in detections)

        if has_candles:
            insights.append("Candlestick chart detected - analyzing price action patterns")
        if has_lines:
            insights.append("Trend lines identified - potential support/resistance levels")
        if has_indicators:
            insights.append("Technical indicators present - momentum analysis available")

        return insights

    def _analyze_market_news(self, detection_result: Dict) -> List[str]:
        """Analyze market news images"""
        insights = []
        detections = detection_result.get("detections", [])

        # Look for text elements
        text_elements = [d for d in detections if "text" in d["class_name"].lower()]

        if text_elements:
            insights.append(f"Detected {len(text_elements)} text regions - potential news headlines")

        # Look for charts/graphs
        chart_elements = [d for d in detections if d["class_name"].lower() in ["chart", "graph", "plot"]]

        if chart_elements:
            insights.append(f"Found {len(chart_elements)} charts - market data visualization detected")

        return insights

    def _general_image_insights(self, detection_result: Dict) -> List[str]:
        """General image insights"""
        insights = []
        detections = detection_result.get("detections", [])

        if detections:
            # Group by class
            class_counts = {}
            for d in detections:
                class_name = d["class_name"]
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            # Generate insights
            for class_name, count in class_counts.items():
                insights.append(f"Detected {count} {class_name}{'s' if count > 1 else ''}")

        return insights

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def health_check(self) -> Dict:
        """Check vision service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            health = {
                "status": "healthy",
                "yolo": {
                    "model": self.yolo_config['model'],
                    "available": self.yolo_model is not None
                },
                "stable_diffusion": {
                    "model": self.diffusers_config['model'],
                    "available": self.diffusers_pipe is not None,
                    "device": self.diffusers_config['device']
                }
            }

            return health

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }