"""
InfinityAI.Pro — Event-Driven Macro Alternative Data Miner (Engine B)
====================================================================
Engine B | Category: Macro Alternative Data Mining | Version: 2.5.0

Mines, interprets, and scores high-impact macroeconomic and central bank announcements:
  1. RBI Monetary Policy Committee (MPC) rate decisions, stance, and governor speeches.
  2. US Federal Reserve FOMC rate decisions and Fed Chair press conferences.
  3. Union Budget, fiscal deficit announcements, and SEBI regulatory circulars.

Architecture & Guardrails:
  - Deep Reasoning via Vertex AI Gemini 2.5 Flash Thinking Budget (1024 tokens).
  - Grounding with Google Search for instant indexation of Indian financial press.
  - Strict Pydantic JSON schema validation.
  - Fail-Safe Circuit Breaker: Automatically falls back to neutral baseline on any API or parse error.
  - Asynchronous Firestore persistence to collection `macro_alternative_data`.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger("InfinityAI.MacroEventMiner")

# ─── Structured Output Schema ────────────────────────────────────────────────
class MacroEventPayload(BaseModel):
    event_name: str = Field(default="GENERAL_MACRO_EVENT", description="Identifier of the policy event")
    timestamp_utc: str = Field(default="", description="ISO timestamp of analysis")
    hawkish_score: float = Field(
        default=0.0,
        description="Sentiment score from -1.0 (ultra dovish) to +1.0 (ultra hawkish)"
    )
    volatility_expectation: str = Field(
        default="MEDIUM",
        description="Volatility regime: LOW, MEDIUM, HIGH, or EXTREME"
    )
    regime_multiplier: float = Field(
        default=1.0,
        description="Suggested Dynamic VaR volatility floor multiplier (1.0 to 3.0)"
    )
    key_drivers: List[str] = Field(
        default_factory=lambda: ["Neutral baseline policy prior"],
        description="Top 3-4 key economic or monetary drivers"
    )
    summary: str = Field(
        default="Neutral baseline state maintained. Standard risk limits active.",
        description="2-sentence institutional summary of policy stance"
    )
    is_fallback: bool = Field(
        default=False,
        description="True if circuit breaker triggered fallback state"
    )


# ─── Event Miner Implementation ──────────────────────────────────────────────
class MacroEventMiner:
    """
    Event-driven alternative data mining engine using Vertex AI Gemini 2.5 with Google Search Grounding.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
        self.genai_client = None
        self.db = None
        self._cached_payload: Optional[MacroEventPayload] = None
        self._last_mined_time: Optional[datetime] = None

        self._init_vertex_ai()
        self._init_firestore()

    def _init_vertex_ai(self) -> None:
        """Initializes Vertex AI Gemini Client with Application Default Credentials (ADC) or API Key."""
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.genai_client = genai.Client(api_key=api_key)
                logger.info("[MacroEventMiner] GenAI client initialized via API Key.")
            else:
                self.genai_client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location="asia-south1"
                )
                logger.info(f"[MacroEventMiner] GenAI client initialized with Vertex AI ADC (Project: {self.project_id}).")
        except Exception as e:
            logger.warning(f"[MacroEventMiner] GenAI client initialization note: {e}")
            self.genai_client = None

    def _init_firestore(self) -> None:
        """Initializes Firestore Client."""
        try:
            from google.cloud import firestore
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"[MacroEventMiner] Firestore client initialized (Project: {self.project_id}).")
        except Exception as e:
            logger.warning(f"[MacroEventMiner] Firestore client note: {e}")
            self.db = None

    def _get_neutral_fallback(self, event_name: str, reason: str) -> MacroEventPayload:
        """
        Circuit Breaker / Fail-Safe Default:
        Emits a mathematically safe neutral payload if any model or network error occurs.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        logger.warning(f"[CIRCUIT BREAKER] Returning neutral macro state for '{event_name}'. Reason: {reason}")
        return MacroEventPayload(
            event_name=event_name,
            timestamp_utc=now_iso,
            hawkish_score=0.0,
            volatility_expectation="MEDIUM",
            regime_multiplier=1.0,
            key_drivers=["Neutral fallback active", f"Diagnostics: {reason[:120]}"],
            summary="Neutral baseline policy state active. Standard quantitative risk limits enforced without disruption.",
            is_fallback=True,
        )

    def mine_event(self, event_query: str, event_name: str = "RBI_MPC_POLICY") -> MacroEventPayload:
        """
        Executes event-driven scraping and reasoning using Gemini 2.5 Flash + Google Search Grounding.
        """
        now_utc = datetime.now(timezone.utc)
        logger.info(f"[MacroEventMiner] Mining live event: '{event_query}' (Event: {event_name})")

        if not self.genai_client:
            fallback = self._get_neutral_fallback(event_name, "GenAI Client unavailable")
            self._cached_payload = fallback
            self._last_mined_time = now_utc
            return fallback

        system_instruction = (
            "You are an institutional quantitative macroeconomic analyst specializing in Indian capital markets "
            "(NSE Nifty 50, BankNifty derivatives, and MCX commodities). "
            "Your objective is to read live policy statements, press conferences, and repo rate actions to extract "
            "a precise hawkish/dovish score and expected market volatility shock. "
            "Reason through nuances:\n"
            "- A rate pause accompanied by 'withdrawal of accommodation' or higher inflation projections is NET HAWKISH.\n"
            "- A surprise liquidity injection or dovish voting split (e.g. 4-2 vs 6-0) is NET DOVISH.\n"
            "Always output strictly compliant JSON according to the schema."
        )

        user_prompt = (
            f"Search for live updates, official press releases, and analyst commentary regarding: '{event_query}'.\n"
            f"Current UTC Time: {now_utc.isoformat()}\n"
            "Synthesize the policy stance, evaluate interest rate implications for Indian equities/derivatives, "
            "and compute: hawkish_score (-1.0 to 1.0), volatility_expectation (LOW, MEDIUM, HIGH, EXTREME), "
            "and regime_multiplier (1.0 to 3.0 for dynamic VaR risk floor scaling)."
        )

        try:
            from google.genai import types

            # Configure deep reasoning with Thinking Budget & Google Search Grounding
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                response_schema=MacroEventPayload,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=1024
                ),
            )

            response = self.genai_client.models.generate_content(
                model=os.getenv("GEMINI_MODEL_ID", "gemini-3.6-flash"),
                contents=user_prompt,
                config=config,
            )

            if not response.text:
                fallback = self._get_neutral_fallback(event_name, "Empty response received from Vertex AI")
                self._cached_payload = fallback
                self._last_mined_time = now_utc
                return fallback

            # Parse and validate against Pydantic schema
            payload = MacroEventPayload.model_validate_json(response.text)
            payload.event_name = event_name
            payload.timestamp_utc = now_utc.isoformat()
            payload.is_fallback = False

            # Strict numerical guardrails
            payload.hawkish_score = max(-1.0, min(1.0, float(payload.hawkish_score)))
            payload.regime_multiplier = max(1.0, min(3.0, float(payload.regime_multiplier)))

            # Cache payload in memory
            self._cached_payload = payload
            self._last_mined_time = now_utc

            logger.info(
                f"[MacroEventMiner Success] Event: {event_name} | "
                f"Hawkish: {payload.hawkish_score:+.2f} | "
                f"Vol: {payload.volatility_expectation} | "
                f"Regime Multiplier: {payload.regime_multiplier:.2f}x"
            )

            # Persist to Firestore asynchronously
            self.push_to_firestore(payload)
            return payload

        except Exception as e:
            fallback = self._get_neutral_fallback(event_name, f"Exception during mining: {e}")
            self._cached_payload = fallback
            self._last_mined_time = now_utc
            return fallback

    def push_to_firestore(self, payload: MacroEventPayload) -> None:
        """Pushes structured macro alternative data to Firestore collection `macro_alternative_data`."""
        if not self.db:
            logger.debug("Firestore client not available for persistence.")
            return

        try:
            from google.cloud import firestore
            doc_data = payload.model_dump()
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP

            # 1. Update active document
            doc_ref = self.db.collection("macro_alternative_data").document("latest_policy_sentiment")
            doc_ref.set(doc_data)

            # 2. Append to historical audit log
            history_id = f"{payload.event_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            self.db.collection("macro_alternative_data").document("audit_history").collection("events").document(history_id).set(doc_data)

            logger.info("[Firestore Synced] Updated `macro_alternative_data/latest_policy_sentiment`.")
        except Exception as e:
            logger.warning(f"[Firestore Warning] Persistence notice: {e}")

    def get_latest_sentiment(self, max_age_hours: float = 4.0) -> MacroEventPayload:
        """
        Reads latest sentiment from memory cache or Firestore.
        If data is older than `max_age_hours`, returns baseline neutral state.
        """
        now_utc = datetime.now(timezone.utc)

        # Check in-memory cache first
        if self._cached_payload and self._last_mined_time:
            age_hours = (now_utc - self._last_mined_time).total_seconds() / 3600.0
            if age_hours <= max_age_hours:
                return self._cached_payload

        # Fallback to reading Firestore
        if self.db:
            try:
                doc = self.db.collection("macro_alternative_data").document("latest_policy_sentiment").get()
                if doc.exists:
                    data = doc.to_dict()
                    payload = MacroEventPayload(**data)
                    self._cached_payload = payload
                    self._last_mined_time = now_utc
                    return payload
            except Exception as e:
                logger.debug(f"Firestore read note: {e}")

        # Return default neutral
        return self._get_neutral_fallback("NO_ACTIVE_EVENT", "No fresh policy event recorded")


# Global singleton instance
macro_event_miner = MacroEventMiner()
