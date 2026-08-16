import os
from google.cloud import secretmanager
from google import genai

print("=== Fetch GEMINI_API_KEY from Secret Manager ===")
sm_client = secretmanager.SecretManagerServiceClient()
secret_name = "projects/project-841b7f97-5ee3-4fbe-920/secrets/GEMINI_API_KEY/versions/latest"
response = sm_client.access_secret_version(name=secret_name)
api_key = response.payload.data.decode("UTF-8").strip()
print("✓ Successfully retrieved GEMINI_API_KEY from Secret Manager (Key Length:", len(api_key), ")")

client = genai.Client(api_key=api_key)
prompt = "Analyze macroeconomic sentiment for Indian equities based on recent RBI MPC decisions. Provide 2 concise bullets."

for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
    try:
        print(f"\n--- Testing Model: {model_name} ---")
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        print("Gemini Response:\n", resp.text)
        print(f"✓ Model {model_name} verified successfully!")
        break
    except Exception as e:
        print(f"Notice for {model_name}:", e)
