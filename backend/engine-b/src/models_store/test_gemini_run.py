import os
from google.cloud import secretmanager
from google import genai

sm = secretmanager.SecretManagerServiceClient()
name = 'projects/project-841b7f97-5ee3-4fbe-920/secrets/GEMINI_API_KEY/versions/latest'
key = sm.access_secret_version(name=name).payload.data.decode('UTF-8').strip()

client = genai.Client(api_key=key)
prompt = 'Summarize Indian capital markets macro sentiment in 2 short bullet points for algorithmic trading.'

for m in ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-pro-latest']:
    try:
        res = client.models.generate_content(model=m, contents=prompt)
        print(f"=== Gemini ({m}) Response ===")
        print(res.text)
        print(f"✓ Model {m} verified successfully!\n")
        break
    except Exception as e:
        print(f"Notice for {m}: {e}")
