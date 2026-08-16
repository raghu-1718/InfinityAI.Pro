import os
from google.cloud import dialogflowcx_v3 as dialogflow

project_id = "project-841b7f97-5ee3-4fbe-920"

# Check both common regions Vertex AI uses
locations = ["us", "global"]

print("🔍 Searching for your Agent's true internal ID...")

for loc in locations:
    try:
        api_endpoint = f"{loc}-dialogflow.googleapis.com:443" if loc != "global" else "dialogflow.googleapis.com:443"
        client = dialogflow.AgentsClient(client_options={"api_endpoint": api_endpoint})
        parent = f"projects/{project_id}/locations/{loc}"

        agents = client.list_agents(parent=parent)
        for agent in agents:
            print(f"\n✅ FOUND IT!")
            print(f"Display Name: {agent.display_name}")
            print(f"Exact Agent Path: {agent.name}")
            print(f"Location to use: {loc}")

    except Exception as e:
        pass # Ignore region errors, we just want to find where it lives

print("\nSearch complete.")
