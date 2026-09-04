import os
import re
from google import genai
from google.genai import types

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
LOCATION_ID = "asia-south1"

def apply_ml_and_ingestion_updates():
    print("🚀 Initializing Gemini 2.5 Flash Executing Agent for ML & Data Ingestion...")

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION_ID)
    model_id = "gemini-2.5-flash"

    prompt = """
    You are the Principal ML Engineer for InfinityAI.Pro.
    Your task is to provide the COMPLETE, final Python code for two critical files. Do not truncate the code. Provide the full file contents.

    ### 1. `options_chain_ingestor.py`
    Provide the full code for `backend/engine-c/src/options_chain_ingestor.py` using the exact optimizations we agreed upon:
    - Use `DhanClient` wrapper for the `option_chain` method.
    - Use direct `requests.post` with an 8-second timeout for the `expirylist` endpoint.
    - Handle malformed strikes safely.
    - Use BigQuery streaming inserts (batch size 500).
    Enclose the code in a markdown block starting with ```python filepath="backend/engine-c/src/options_chain_ingestor.py"

    ### 2. `train_tri_model.py`
    Provide the full code for `backend/engine-b/src/training/train_tri_model.py`.
    You MUST implement the following two features:

    A. The `calculate_features(df_ohlcv, df_options)` function:
       It must convert `df_options['timestamp']` to date, aggregate `open_interest` by `option_type` to get `Total_CE_OI` and `Total_PE_OI`, calculate `PCR` (PE_OI / CE_OI handling zero division), and merge it into `df_ohlcv` using forward fill (`ffill`).

    B. The `fetch_options_features_from_bigquery(symbol)` function:
       It must implement Compute Engine VM local caching. Check if `local_cache/options_data_{symbol}.parquet` exists and is less than 24 hours old. If so, load it via `pd.read_parquet`. If not, run the BigQuery extraction from `market_data.options_ticks`, save it locally to the `.parquet` file to save egress costs, and return the DataFrame.

    Enclose the code in a markdown block starting with ```python filepath="backend/engine-b/src/training/train_tri_model.py"
    """

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    print(f"\n📡 Streaming full codebase implementations from {model_id}...\n" + "="*70)

    response_stream = client.models.generate_content_stream(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(max_output_tokens=8192, temperature=0.1),
    )

    full_response = ""
    for chunk in response_stream:
        if chunk.text:
            print(chunk.text, end="")
            full_response += chunk.text

    print("\n" + "="*70)
    print("💾 Extracting and saving files to workspace...")

    # Regex to extract filepaths and code blocks
    pattern = r"```python\s+filepath=\"([^\"]+)\"\n(.*?)```"
    matches = re.finditer(pattern, full_response, re.DOTALL)

    saved_files = 0
    for match in matches:
        filepath = match.group(1).strip()
        code = match.group(2).strip()

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Write the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"  ✅ Successfully updated: {filepath}")
        saved_files += 1

    # Ensure the local cache directory exists for Engine-B
    os.makedirs("backend/engine-b/src/training/local_cache", exist_ok=True)
    print("  ✅ Ensured Engine-B local cache directory exists.")

    if saved_files == 0:
        print("⚠️ No files were extracted. Check the output format.")
    else:
        print(f"\n🎉 Done! {saved_files} files written. The ML Pipeline and Data Ingestion are now fully optimized.")

if __name__ == "__main__":
    apply_ml_and_ingestion_updates()
