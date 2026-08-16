import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import bigquery

try:
    from shared.google_integrations import EnhancedGenAIClient
    HAS_ENHANCED_GENAI = True
except ImportError:
    HAS_ENHANCED_GENAI = False

router = APIRouter()
logger = logging.getLogger(__name__)

class OptionsAnalysisRequest(BaseModel):
    ticker: str

# Initialize clients
bq_client = None
try:
    bq_client = bigquery.Client()
    logger.info("✅ BigQuery client initialized for market analysis route.")
except Exception as e:
    logger.error(f"❌ Failed to initialize BigQuery client: {e}")

genai_client = None
if HAS_ENHANCED_GENAI:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "infinity-ai-pro-dev")
        genai_client = EnhancedGenAIClient(project_id=PROJECT_ID)
        logger.info("✅ EnhancedGenAIClient initialized for market analysis route.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize EnhancedGenAIClient: {e}")

@router.post("/analyze-options", tags=["Market Analysis"])
async def analyze_options_data(request: OptionsAnalysisRequest):
    if not bq_client or not genai_client:
        raise HTTPException(status_code=503, detail="A backend service is not configured (BigQuery or GenAI).")

    ticker = request.ticker
    try:
        # 1. Fetch data from BigQuery
        query = f"""
            SELECT *
            FROM `project-841b7f97-5ee3-4fbe-920.market_data.options_ticks`
            WHERE underlying = @ticker
            ORDER BY timestamp DESC
            LIMIT 5
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker),
            ]
        )
        query_job = bq_client.query(query, job_config=job_config)
        rows = list(query_job.result())

        if not rows:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {ticker}")

        # 2. Format data into a string
        data_string = "Latest options tick data:\n"
        for row in rows:
            data_string += f"- {dict(row)}\n"

        # 3. Create prompt and call Gemini
        prompt = f"""
        Analyze the following recent options tick data for {ticker}. Provide institutional-grade algorithmic trading insights, focusing specifically on Open Interest (OI) build-up and Implied Volatility (IV) shifts. What do these patterns suggest about market sentiment and potential price movements?

        Data:
        {data_string}

        Your analysis should be concise, actionable, and suitable for an automated trading system.
        """

        # Using the chat method which seems to be for free-form text.
        response = await genai_client.chat(prompt)
        ai_response = response.get("response", "No response from AI.")

        return {"analysis": ai_response}

    except Exception as e:
        logger.error(f"Error in options analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
