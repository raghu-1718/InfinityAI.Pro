import os
from google import genai
from google.genai import types

print("=== Testing Vertex AI Gemini 2.5 Flash Grounding ===")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")

try:
    client = genai.Client(vertexai=True, project=project_id, location="asia-south1")
    prompt = "Summarize current Indian monetary policy stance by RBI in 2 bullet points for quantitative equity trading."
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    print("Gemini 2.5 Flash Response:\n", response.text)
    print("\n✓ Vertex AI Gemini 2.5 Flash successfully executed via Application Default Credentials (ADC)!")
except Exception as e:
    print("Gemini Notice/Fallback:", e)
