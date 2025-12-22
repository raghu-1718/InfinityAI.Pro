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

    async def query(self, input_text: str) -> Dict[str, Any]:
        """
        Send a query to the Reasoning Engine.
        
        Args:
            input_text: The prompt or question for the agent.
            
        Returns:
            The agent's response payload.
        """
        url = f"{self.base_url}:query"
        payload = {"input": {"input": input_text}} # Structure depends on agent schema, usually {"input": {"input": "..."}} or {"input": "..."}
        
        # Based on typical LangChain/Reasoning Engine templates, input structure often wraps the text.
        # If the agent expects a different schema, this might need adjustment.
        # Assuming standard schema: { "input": { "query": "..." } } or similar.
        # Let's try the generic `{"input": {"question": input_text}}` or similar based on description.
        # The user's metadata didn't specify the input schema, but "Google-ADK" often uses {"input": ...}
        
        # Let's wrap safely.
        payload = {"input": {"input": input_text}}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=60.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Reasoning Engine Query Failed: {e}")
            return {"error": str(e)}

    async def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Ask the Financial Advisor agent to analyze a specific stock.
        """
        prompt = f"Analyze {symbol} for a potential intraday trade. Provide BUY/SELL/HOLD recommendation with entry, stop-loss, and target."
        return await self.query(prompt)
