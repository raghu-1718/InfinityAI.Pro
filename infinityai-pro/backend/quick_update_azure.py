#!/usr/bin/env python3
import os
from pathlib import Path

# Get Azure OpenAI key from user
azure_key = input("Paste your Azure OpenAI KEY 1: ").strip()

if not azure_key or azure_key == "your_azure_openai_key_here":
    print("❌ Please provide a valid Azure OpenAI key")
    exit(1)

# Update .env file
env_file = Path(".env")
content = env_file.read_text()
content = content.replace("AZURE_OPENAI_KEY=your_azure_openai_key_here", f"AZURE_OPENAI_KEY={azure_key}")
env_file.write_text(content)

print("✅ Azure OpenAI key updated!")

# Test the configuration
os.environ["AZURE_OPENAI_KEY"] = azure_key
print("🔍 Testing AI services...")

try:
    from services.cloud_ai_manager import cloud_ai_manager
    import asyncio
    
    async def test():
        success = await cloud_ai_manager.initialize()
        status = cloud_ai_manager.get_service_status()
        return success, status
    
    success, status = asyncio.run(test())
    print(f"✅ AI services initialized: {success}")
    print(f"Available services: {status['available_services']}")
    
    if success:
        print("🎉 Your multi-cloud AI trading system is ready!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
