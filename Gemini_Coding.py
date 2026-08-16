import os
from google import genai
from google.genai import types

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
LOCATION_ID = "asia-south1"

def execute_refactor():
    print("🚀 Commanding Gemini 2.5 Flash to execute the refactor plan...")

    # Read the generated refactor plan
    if not os.path.exists("REFACTOR_PLAN.md"):
        print("❌ REFACTOR_PLAN.md not found. Please run the planning script first.")
        return

    with open("REFACTOR_PLAN.md", "r", encoding="utf-8") as f:
        plan_content = f.read()

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
    model_id = "gemini-2.5-flash"

    prompt = f"""
    You are the Autonomous Refactoring Agent for InfinityAI.Pro.
    Based on the following `REFACTOR_PLAN.md`, your job is to output the exact Python code blocks, shell commands, or file content updates required to apply these changes.
    Specifically, generate the complete content for the new master documentation file `SYSTEM_ARCHITECTURE.md`, and provide clear execution steps.

    --- REFACTOR PLAN ---
    {plan_content}
    """

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    response_stream = client.models.generate_content_stream(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(max_output_tokens=8192, temperature=0.1),
    )

    execution_output = ""
    print("\n" + "="*70 + "\nExecuting Refactor & Generating Master Documentation...\n" + "="*70)
    for chunk in response_stream:
        if chunk.text:
            print(chunk.text, end="")
            execution_output += chunk.text

    # Automatically save the master architecture doc
    with open("SYSTEM_ARCHITECTURE.md", "w", encoding="utf-8") as f:
        f.write(execution_output)

    print("\n" + "="*70)
    print("✅ SYSTEM_ARCHITECTURE.md successfully generated and saved to workspace root!")

if __name__ == "__main__":
    execute_refactor()
