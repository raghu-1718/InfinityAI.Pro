import sys
import os
import asyncio

# Add engine-c src to python path
sys.path.append(os.path.abspath(os.path.join("backend", "engine-c")))

from src.options_chain_ingestor import options_ingestor

async def main():
    print("🚀 Triggering live options chain ingestion from Dhan to BigQuery...")
    result = await options_ingestor.ingest_live_option_chains("raghu_primary")
    print("📊 Ingestion Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
