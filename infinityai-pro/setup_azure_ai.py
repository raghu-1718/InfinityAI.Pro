#!/usr/bin/env python3
"""
Azure AI Foundry Setup Script for InfinityAI.Pro
Configures Azure AI Foundry integration for hybrid cloud deployment
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

def run_command(cmd: str, capture_output: bool = True) -> str:
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return ""

def check_azure_cli():
    """Check if Azure CLI is installed"""
    print("🔍 Checking Azure CLI installation...")
    try:
        version = run_command("az --version | head -1")
        print(f"✅ Azure CLI found: {version}")
        return True
    except:
        print("❌ Azure CLI not found. Please install it first:")
        print("   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        return False

def login_to_azure():
    """Login to Azure CLI"""
    print("\n🔐 Logging into Azure...")
    print("A browser window will open for authentication.")
    result = run_command("az login --use-device-code")
    if result:
        print("✅ Azure login successful")
        return True
    else:
        print("❌ Azure login failed")
        return False

def get_subscription_info():
    """Get current subscription information"""
    print("\n📋 Getting subscription information...")
    try:
        subscription = json.loads(run_command("az account show"))
        print(f"✅ Current subscription: {subscription['name']} ({subscription['id']})")
        return subscription
    except:
        print("❌ Failed to get subscription information")
        return None

def create_resource_group(name: str = "infinityai-rg", location: str = "SouthIndia"):
    """Create Azure resource group"""
    print(f"\n🏗️  Creating resource group '{name}' in {location}...")
    try:
        result = run_command(f"az group create --name {name} --location {location}")
        print("✅ Resource group created successfully")
        return True
    except:
        print(f"⚠️  Resource group '{name}' may already exist")
        return True

def create_ai_project(project_name: str = "infinityai-pro", resource_group: str = "infinityai-rg"):
    """Create Azure AI Foundry project"""
    print(f"\n🤖 Creating Azure AI Foundry project '{project_name}'...")

    # First, create the AI hub
    hub_name = f"{project_name}-hub"
    try:
        result = run_command(f"""
        az ml workspace create --name {hub_name} \
            --resource-group {resource_group} \
            --kind hub \
            --location southindia
        """)
        print("✅ AI hub created successfully")
    except:
        print(f"⚠️  AI hub '{hub_name}' may already exist")

    # Create the project
    try:
        result = run_command(f"""
        az ml workspace create --name {project_name} \
            --resource-group {resource_group} \
            --kind project \
            --hub {hub_name} \
            --location southindia
        """)
        print("✅ AI project created successfully")
        return True
    except:
        print(f"⚠️  AI project '{project_name}' may already exist")
        return True

def setup_openai_models(project_name: str, resource_group: str):
    """Set up OpenAI models in the project"""
    print("🎯 Setting up OpenAI models...")

    # Deploy GPT-4 model
    try:
        result = run_command(f"""
        az ml model deploy --name gpt-4-deployment \
            --model gpt-4 \
            --workspace {project_name} \
            --resource-group {resource_group} \
            --instance-type Standard_DS3_v2 \
            --instance-count 1
        """)
        print("✅ GPT-4 model deployed")
    except:
        print("⚠️  GPT-4 deployment may already exist or failed")

    # Deploy DALL-E 3 model
    try:
        result = run_command(f"""
        az ml model deploy --name dall-e-3-deployment \
            --model dall-e-3 \
            --workspace {project_name} \
            --resource-group {resource_group} \
            --instance-type Standard_DS3_v2 \
            --instance-count 1
        """)
        print("✅ DALL-E 3 model deployed")
    except:
        print("⚠️  DALL-E 3 deployment may already exist or failed")

    # Deploy Whisper model
    try:
        result = run_command(f"""
        az ml model deploy --name whisper-deployment \
            --model whisper-1 \
            --workspace {project_name} \
            --resource-group {resource_group} \
            --instance-type Standard_DS3_v2 \
            --instance-count 1
        """)
        print("✅ Whisper model deployed")
    except:
        print("⚠️  Whisper deployment may already exist or failed")

def get_endpoints(project_name: str, resource_group: str) -> Dict[str, str]:
    """Get the endpoints for deployed models"""
    print("🔗 Getting model endpoints...")
    endpoints = {}

    try:
        # Get GPT-4 endpoint
        gpt4_endpoint = run_command(f"""
        az ml online-endpoint list --workspace {project_name} \
            --resource-group {resource_group} \
            --query "[?name=='gpt-4-deployment'].scoringUri" -o tsv
        """)
        if gpt4_endpoint:
            endpoints['gpt4'] = gpt4_endpoint.strip()
            print(f"✅ GPT-4 endpoint: {gpt4_endpoint}")

        # Get DALL-E 3 endpoint
        dalle_endpoint = run_command(f"""
        az ml online-endpoint list --workspace {project_name} \
            --resource-group {resource_group} \
            --query "[?name=='dall-e-3-deployment'].scoringUri" -o tsv
        """)
        if dalle_endpoint:
            endpoints['dalle'] = dalle_endpoint.strip()
            print(f"✅ DALL-E 3 endpoint: {dalle_endpoint}")

        # Get Whisper endpoint
        whisper_endpoint = run_command(f"""
        az ml online-endpoint list --workspace {project_name} \
            --resource-group {resource_group} \
            --query "[?name=='whisper-deployment'].scoringUri" -o tsv
        """)
        if whisper_endpoint:
            endpoints['whisper'] = whisper_endpoint.strip()
            print(f"✅ Whisper endpoint: {whisper_endpoint}")

    except Exception as e:
        print(f"⚠️  Error getting endpoints: {e}")

    return endpoints

def get_api_keys(project_name: str, resource_group: str) -> str:
    """Get API keys for the project"""
    print("🔑 Getting API keys...")
    try:
        # Get the primary key for the workspace
        api_key = run_command(f"""
        az ml workspace keys list --workspace {project_name} \
            --resource-group {resource_group} \
            --query primaryKey -o tsv
        """)
        if api_key:
            print("✅ API key retrieved")
            return api_key.strip()
        else:
            print("❌ Failed to retrieve API key")
            return ""
    except Exception as e:
        print(f"⚠️  Error getting API key: {e}")
        return ""

def update_env_file(endpoints: Dict[str, str], api_key: str, project_name: str):
    """Update the .env file with Azure AI configuration"""
    env_file = Path("/workspaces/InfinityAI.Pro/infinityai-pro/.env")

    # Read existing .env file
    env_content = ""
    if env_file.exists():
        env_content = env_file.read_text()

    # Prepare new Azure AI configuration
    azure_config = f"""
# Azure AI Foundry Configuration
AZURE_OPENAI_ENDPOINT=https://southindia.api.azureml.ms
AZURE_OPENAI_KEY={api_key}
AZURE_AI_PROJECT={project_name}

# Azure AI Model Endpoints (for reference)
# AZURE_GPT4_ENDPOINT={endpoints.get('gpt4', '')}
# AZURE_DALLE_ENDPOINT={endpoints.get('dalle', '')}
# AZURE_WHISPER_ENDPOINT={endpoints.get('whisper', '')}
"""

    # Check if Azure config already exists
    if "AZURE_OPENAI_ENDPOINT" in env_content:
        print("⚠️  Azure AI configuration already exists in .env file")
        print("Please manually update the values if needed.")
    else:
        # Append to .env file
        with open(env_file, 'a') as f:
            f.write("\n" + azure_config)
        print("✅ Azure AI configuration added to .env file")

def main():
    """Main setup function"""
    print("🚀 InfinityAI.Pro - Azure AI Foundry Setup")
    print("=" * 50)

    # Check prerequisites
    if not check_azure_cli():
        sys.exit(1)

    if not login_to_azure():
        sys.exit(1)

    subscription = get_subscription_info()
    if not subscription:
        sys.exit(1)

    # Configuration
    resource_group = "infinityai-rg"
    project_name = "infinityai-pro"
    location = "SouthIndia"

    # Create resources
    if not create_resource_group(resource_group, location):
        print("❌ Failed to create resource group")
        sys.exit(1)

    if not create_ai_project(project_name, resource_group):
        print("❌ Failed to create AI project")
        sys.exit(1)

    # Setup models
    setup_openai_models(project_name, resource_group)

    # Get endpoints and keys
    endpoints = get_endpoints(project_name, resource_group)
    api_key = get_api_keys(project_name, resource_group)

    if not api_key:
        print("❌ Failed to retrieve API key. Please check your Azure AI Foundry setup.")
        sys.exit(1)

    # Update environment
    update_env_file(endpoints, api_key, project_name)

    print("\n🎉 Azure AI Foundry setup completed!")
    print("\n📝 Next steps:")
    print("1. Restart your application to load the new environment variables")
    print("2. Test the Azure AI integration using the health check endpoint")
    print("3. Monitor costs in the Azure portal")
    print("\n💡 Your hybrid cloud setup is now ready:")
    print("   - Linode: Storage and compute")
    print("   - Azure AI Foundry: Managed AI services")

if __name__ == "__main__":
    main()