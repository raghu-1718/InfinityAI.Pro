# services/ai/stt_service.py
"""
InfinityAI.Pro - Speech-to-Text Service
Whisper integration for audio transcription
"""

import os
import tempfile
import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-Text service using Whisper"""

    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.initialized = False

    async def initialize(self):
        """Initialize Whisper model"""
        try:
            import whisper

            logger.info(f"Loading Whisper model: {self.config['model']}")
            self.model = whisper.load_model(self.config['model'])

            self.initialized = True
            logger.info("✅ STT Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize STT service: {e}")
            raise

    async def close(self):
        """Close STT service"""
        # Whisper models don't need explicit closing
        pass

    async def transcribe(self, audio_data: bytes, filename: str = None) -> Dict:
        """Transcribe audio to text"""
        try:
            if not self.initialized:
                raise RuntimeError("STT service not initialized")

            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".wav" if filename and filename.endswith('.wav') else ".mp3",
                delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # Transcribe audio
                result = self.model.transcribe(
                    temp_path,
                    language=self.config.get('language'),
                    task="transcribe"
                )

                # Extract key information
                transcription = {
                    "text": result.get("text", "").strip(),
                    "language": result.get("language"),
                    "confidence": self._calculate_confidence(result),
                    "segments": self._format_segments(result.get("segments", [])),
                    "duration": result.get("duration", 0),
                    "timestamp": self._get_timestamp()
                }

                return transcription

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error in speech transcription: {e}")
            return {"error": str(e)}

    async def transcribe_file(self, file_path: str) -> Dict:
        """Transcribe audio from file path"""
        try:
            if not self.initialized:
                raise RuntimeError("STT service not initialized")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Transcribe audio
            result = self.model.transcribe(
                file_path,
                language=self.config.get('language'),
                task="transcribe"
            )

            transcription = {
                "text": result.get("text", "").strip(),
                "language": result.get("language"),
                "confidence": self._calculate_confidence(result),
                "segments": self._format_segments(result.get("segments", [])),
                "duration": result.get("duration", 0),
                "file_path": file_path,
                "timestamp": self._get_timestamp()
            }

            return transcription

        except Exception as e:
            logger.error(f"Error transcribing file {file_path}: {e}")
            return {"error": str(e)}

    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate overall confidence score"""
        try:
            segments = result.get("segments", [])
            if not segments:
                return 0.0

            # Average confidence across all segments
            total_confidence = sum(segment.get("confidence", 0) for segment in segments)
            return total_confidence / len(segments)

        except Exception:
            return 0.0

    def _format_segments(self, segments: list) -> list:
        """Format segments for API response"""
        formatted = []
        for segment in segments:
            formatted.append({
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "confidence": segment.get("confidence", 0)
            })
        return formatted

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def health_check(self) -> Dict:
        """Check STT service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            # Check if model is loaded
            if self.model is None:
                return {"status": "error", "error": "Model not loaded"}

            return {
                "status": "healthy",
                "model": self.config['model'],
                "language": self.config.get('language')
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }