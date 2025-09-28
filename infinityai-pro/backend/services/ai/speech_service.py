# services/ai/speech_service.py
"""
InfinityAI.Pro - Multi-Cloud Speech Service
Supports Azure Cognitive Services (primary), AWS Transcribe (secondary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime
import base64
import io
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class SpeechService:
    """Multi-cloud speech service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False

    async def initialize(self):
        """Initialize multi-cloud speech connections"""
        try:
            self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for audio processing
            self.initialized = True
            logger.info("✅ Multi-cloud Speech Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Speech service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Azure Speech (Primary)
    async def azure_transcribe(self, audio_data: bytes, **kwargs) -> str:
        """Azure Speech-to-Text transcription"""
        try:
            azure_url = f"{self.config.AZURE_SPEECH_ENDPOINT}/speechtotext/transcriptions:transcribe?api-version=2024-05-15-preview"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_SPEECH_KEY,
                "Content-Type": "audio/wav"
            }

            params = {
                "language": kwargs.get("language", "en-US"),
                "format": "detailed"
            }

            async with self.client.post(azure_url, data=audio_data, headers=headers, params=params) as resp:
                resp.raise_for_status()
                result = resp.json()

            # Extract transcription
            if result.get("recognizedPhrases"):
                return result["recognizedPhrases"][0].get("nBest", [{}])[0].get("display", "")
            return ""

        except Exception as e:
            logger.error(f"Azure Speech transcription error: {e}")
            raise

    async def azure_synthesize(self, text: str, **kwargs) -> bytes:
        """Azure Text-to-Speech synthesis"""
        try:
            azure_url = f"{self.config.AZURE_SPEECH_ENDPOINT}/texttospeech/v3.0/speak"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_SPEECH_KEY,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
            }

            ssml = f"""<speak version='1.0' xml:lang='en-US'>
                <voice xml:lang='en-US' xml:gender='Male' name='en-US-AndrewMultilingualNeural'>
                    {text}
                </voice>
            </speak>"""

            async with self.client.post(azure_url, data=ssml, headers=headers) as resp:
                resp.raise_for_status()
                return resp.content

        except Exception as e:
            logger.error(f"Azure Speech synthesis error: {e}")
            raise

            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')

            payload = {
                "input": {
                    "audio": audio_b64,
                    "model": kwargs.get("model", "whisper-large-v3"),
                    "language": kwargs.get("language", "en"),
                    "task": "transcribe"
                }
            }

            async with self.client.post(runpod_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()
                return result.get("output", {}).get("text", "")

        except Exception as e:
            logger.error(f"RunPod Whisper error: {e}")
            raise

    async def runpod_synthesize(self, text: str, **kwargs) -> bytes:
        """RunPod text-to-speech"""
        try:
            runpod_url = self.config.RUNPOD_TTS_ENDPOINT
            headers = {
                "Authorization": f"Bearer {self.config.RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "input": {
                    "text": text,
                    "voice": kwargs.get("voice", "en-US-1"),
                    "speed": kwargs.get("speed", 1.0)
                }
            }

            async with self.client.post(runpod_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()
                # Decode base64 audio
                audio_b64 = result.get("output", {}).get("audio", "")
                return base64.b64decode(audio_b64)

        except Exception as e:
            logger.error(f"RunPod TTS error: {e}")
            raise

    # Azure Cognitive Services (Secondary)
    async def azure_transcribe(self, audio_data: bytes, **kwargs) -> str:
        """Azure Speech-to-Text"""
        try:
            azure_url = f"{self.config.AZURE_SPEECH_ENDPOINT}/speechtotext/transcriptions:transcribe?api-version=2024-05-15-preview"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_SPEECH_KEY,
                "Content-Type": "audio/wav"
            }

            # Azure expects specific audio format, may need conversion
            async with self.client.post(azure_url, data=audio_data, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()
                return result.get("text", "")

        except Exception as e:
            logger.error(f"Azure Speech-to-Text error: {e}")
            raise

    async def azure_synthesize(self, text: str, **kwargs) -> bytes:
        """Azure Text-to-Speech"""
        try:
            azure_url = f"{self.config.AZURE_SPEECH_ENDPOINT}/texttospeech:synthesize?api-version=2024-05-15-preview"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_SPEECH_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "voice": kwargs.get("voice", "en-US-AriaRUS"),
                "format": "audio/wav"
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                return resp.content

        except Exception as e:
            logger.error(f"Azure Text-to-Speech error: {e}")
            raise

    # AWS Transcribe (Secondary)
    async def aws_transcribe(self, audio_data: bytes, **kwargs) -> str:
        """AWS Transcribe"""
        try:
            import boto3
            transcribe = boto3.client(
                'transcribe',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            # Upload audio to S3 first (required for Transcribe)
            s3 = boto3.client('s3', region_name=self.config.AWS_REGION)
            audio_key = f"audio/temp_{datetime.now().timestamp()}.wav"

            s3.put_object(
                Bucket=self.config.AWS_S3_BUCKET,
                Key=audio_key,
                Body=audio_data
            )

            # Start transcription job
            job_name = f"transcription_{datetime.now().timestamp()}"
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f"s3://{self.config.AWS_S3_BUCKET}/{audio_key}"},
                MediaFormat='wav',
                LanguageCode=kwargs.get('language', 'en-US')
            )

            # Wait for completion (simplified - in production use async)
            while True:
                status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break
                await asyncio.sleep(5)

            if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                # Download and parse transcript
                async with self.client.get(transcript_uri) as resp:
                    transcript_data = resp.json()
                    return transcript_data['results']['transcripts'][0]['transcript']

            return ""

        except Exception as e:
            logger.error(f"AWS Transcribe error: {e}")
            raise

    async def aws_synthesize(self, text: str, **kwargs) -> bytes:
        """AWS Polly Text-to-Speech"""
        try:
            import boto3
            polly = boto3.client(
                'polly',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=kwargs.get('voice', 'Joanna')
            )

            return response['AudioStream'].read()

        except Exception as e:
            logger.error(f"AWS Polly error: {e}")
            raise

    # Legacy methods for backward compatibility
    async def transcribe_audio(self, audio_data: bytes, **kwargs) -> str:
        """Transcribe audio using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                return await router.transcribe_audio(audio_data, **kwargs)

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise

    async def synthesize_speech(self, text: str, **kwargs) -> bytes:
        """Synthesize speech using router"""
        try:
            from .router import AIRouter
            async with AIRouter() as router:
                return await router.synthesize_speech(text, **kwargs)

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise

    async def health_check(self) -> Dict:
        """Check speech service health"""
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