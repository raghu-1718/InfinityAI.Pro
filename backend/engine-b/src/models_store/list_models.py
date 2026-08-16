import os
from google.cloud import secretmanager
from google import genai

sm_client = secretmanager.SecretManagerServiceClient()
secret_name = "projects/project-841b7f97-5ee3-4fbe-920/secrets/GEMINI_API_KEY/versions/latest"
response = sm_client.access_secret_version(name=secret_name)
api_key = response.payload.data.decode("UTF-8").strip()

client = genai.Client(api_key=api_key)
print("=== Listing Available Gemini Models ===")
models = client.models.list()
for m in models:
    if "gemini" in m.name.lower():
        print(f"Name: {m.name} | Supported: {m.supported_actions}")
