"""
InfinityAI.Pro — Vertex AI Search (Discovery Engine) Service
============================================================
Provides institutional semantic search and grounding over:
1. Macroeconomic research & RBI monetary policy statements.
2. SEBI regulatory circulars & NSE market notices.
3. Historical EOD trade journal audits and quantitative research.
Utilizes Google Cloud Gen AI Trial for Gen App Builder credits.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("InfinityAI.DiscoverySearch")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LOCATION = os.getenv("DISCOVERY_ENGINE_LOCATION", "global")
ENGINE_ID = os.getenv("DISCOVERY_ENGINE_ID", "infinity-unified-search_1789243631822")
DATA_STORE_ID = os.getenv("DISCOVERY_ENGINE_DATA_STORE_ID", "infinity-quant-search_1789241521838")
COLLECTION_ID = "default_collection"


class DiscoverySearchService:
    """Service wrapper around Vertex AI Search (Discovery Engine API)."""

    def __init__(
        self,
        project_id: str = PROJECT_ID,
        location: str = LOCATION,
        engine_id: str = ENGINE_ID,
        data_store_id: str = DATA_STORE_ID,
    ):
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id
        self.data_store_id = data_store_id
        self._client = None
        self._serving_config = None
        self._init_client()

    def _init_client(self):
        # Target unified engine with both data stores (Enterprise Blended Search)
        if self.engine_id:
            self._serving_config = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"collections/{COLLECTION_ID}/engines/{self.engine_id}/"
                f"servingConfigs/default_search"
            )
        else:
            self._serving_config = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"collections/{COLLECTION_ID}/dataStores/{self.data_store_id}/"
                f"servingConfigs/default_search"
            )

        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            self._client = discoveryengine.SearchServiceClient()
            logger.info(
                f"✅ DiscoverySearchService initialized via gRPC for {self._serving_config}"
            )
        except Exception as e:
            logger.info(
                f"DiscoverySearchService using Google ADC REST fallback for {self._serving_config} ({e})"
            )
            self._client = None

    def _search_via_rest(self, query: str, page_size: int = 5) -> Dict[str, Any]:
        """Direct REST fallback to Discovery Engine API using Application Default Credentials (ADC)."""
        import json
        import urllib.request
        import google.auth
        import google.auth.transport.requests

        try:
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            token = creds.token

            url = f"https://discoveryengine.googleapis.com/v1/{self._serving_config}:search"
            payload = {
                "query": query,
                "pageSize": page_size,
                "contentSearchSpec": {
                    "snippetSpec": {"returnSnippet": True},
                    "summarySpec": {"summaryResultCount": 3, "includeCitations": True}
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "x-goog-user-project": self.project_id
                }
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results: List[Dict[str, Any]] = []
                citations: List[Dict[str, str]] = []

                for item in data.get("results", []):
                    doc = item.get("document", {})
                    struct_data = doc.get("derivedStructData", {})
                    title = struct_data.get("title", doc.get("id", "Macro Research Document"))
                    link = struct_data.get("link", "")
                    snippets = [
                        s.get("snippet", "")
                        for s in struct_data.get("snippets", [])
                        if s.get("snippet")
                    ]
                    results.append({
                        "id": doc.get("id"),
                        "title": title,
                        "link": link,
                        "snippet": snippets[0] if snippets else "",
                    })
                    if link:
                        citations.append({"title": title, "uri": link})

                summary_text = data.get("summary", {}).get("summaryText", "")
                return {
                    "status": "success",
                    "query": query,
                    "summary": summary_text,
                    "results": results,
                    "citations": citations,
                }
        except Exception as e:
            logger.warning(f"REST search execution notice: {e}")
            return {
                "status": "pending_indexing",
                "query": query,
                "summary": "Vertex AI Search data store is currently indexing documents.",
                "results": [],
                "citations": [],
                "note": str(e),
            }

    def search_macro_vault(
        self, query: str, page_size: int = 5
    ) -> Dict[str, Any]:
        """
        Executes semantic search over indexed documents with LLM summarization.
        Returns structured results with citations and document snippets.
        """
        if not self._serving_config:
            self._init_client()

        # If client library is not available, execute via direct REST
        if not self._client:
            return self._search_via_rest(query=query, page_size=page_size)

        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            request = discoveryengine.SearchRequest(
                serving_config=self._serving_config,
                query=query,
                page_size=page_size,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    ),
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=3,
                        include_citations=True,
                    ),
                ),
            )

            response = self._client.search(request=request)

            results: List[Dict[str, Any]] = []
            citations: List[Dict[str, str]] = []

            for item in response.results:
                doc = item.document
                data = doc.derived_struct_data or {}
                title = data.get("title", doc.id or "Macro Research Document")
                link = data.get("link", "")
                snippets = [
                    s.get("snippet", "")
                    for s in data.get("snippets", [])
                    if s.get("snippet")
                ]

                result_entry = {
                    "id": doc.id,
                    "title": title,
                    "link": link,
                    "snippet": snippets[0] if snippets else "",
                }
                results.append(result_entry)

                if link:
                    citations.append({"title": title, "uri": link})

            summary_text = ""
            if hasattr(response, "summary") and response.summary:
                summary_text = response.summary.summary_text

            return {
                "status": "success",
                "query": query,
                "summary": summary_text,
                "results": results,
                "citations": citations,
            }

        except Exception as e:
            logger.info(
                f"Discovery Engine search note for '{query}': {e}. "
                "Data Store may still be awaiting one-time activation in GCP Console."
            )
            return {
                "status": "pending_data_store",
                "query": query,
                "summary": None,
                "results": [],
                "citations": [],
                "note": str(e),
            }


# Singleton instance
_search_service: Optional[DiscoverySearchService] = None


def get_discovery_search_service() -> DiscoverySearchService:
    global _search_service
    if _search_service is None:
        _search_service = DiscoverySearchService()
    return _search_service
