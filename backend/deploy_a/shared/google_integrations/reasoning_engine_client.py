"""
Vertex AI Reasoning Engine Client
=================================
Dedicated client for interacting with deployed Vertex AI Reasoning Engines (GenAI Agents).
Specifically configured for 'financial-advisor-21947'.
"""

import os
import logging
import httpx
import google.auth
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional

logger = logging.getLogger("InfinityAI.ReasoningEngine")

class ReasoningEngineClient:
    """
    Client for interacting with Vertex AI Reasoning Engines.
    
    Target Agent: financial-advisor-21947
    Resource: projects/429140669077/locations/us-central1/reasoningEngines/8753627684120035328
    """
    
    def __init__(self, project_id: str = "429140669077", location: str = "us-central1", agent_id: str = "8753627684120035328"):
        self.project_id = project_id
        self.location = location
        self.agent_id = agent_id
        self.base_url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines/{agent_id}"
        self.creds, _ = google.auth.default()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get Authorization headers with fresh token."""
        if not self.creds.valid:
            self.creds.refresh(Request())
        return {
            "Authorization": f"Bearer {self.creds.token}",
            "Content-Type": "application/json"
        }

    async def invoke_method(self, method_name: str, kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invoke a specific method on the Reasoning Engine.
        """
        url = f"{self.base_url}:{method_name}"
        
        payload = kwargs or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=60.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            if isinstance(e, httpx.HTTPStatusError):
                logger.error(f"❌ Method '{method_name}' Failed: {e.response.text}")
                return {"error": str(e), "details": e.response.text}
            logger.error(f"❌ Reasoning Engine Method '{method_name}' Failed: {e}")
            return {"error": str(e)}

    async def query(self, input_text: str) -> Dict[str, Any]:
        """
        Send a query to the Reasoning Engine.
        """
        return await self.invoke_method("query", {"input": {"input": input_text}})

    async def create_session(self) -> Dict[str, Any]:
        """
        Test method to create a session.
        """
        return await self.invoke_method("create_session", {})

    async def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Ask the Financial Advisor agent to analyze a specific stock.
        """
        prompt = f"Analyze {symbol} for a potential intraday trade. Provide BUY/SELL/HOLD recommendation with entry, stop-loss, and target."
        return await self.query(prompt)
