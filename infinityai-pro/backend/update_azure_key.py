#!/usr/bin/env python3
"""
Update Azure OpenAI key in .env file
"""

import os
from pathlib import Path

def update_env_file():
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        return
    
    # Get the key from user input
    api_key = input("Enter your Azure OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    # Read current content
    content = env_file.read_text()
    
    # Replace the placeholder
    old_line = "AZURE_OPENAI_KEY=your_azure_openai_key_here"
    new_line = f"AZURE_OPENAI_KEY={api_key}"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        env_file.write_text(content)
        print("✅ Azure OpenAI key updated in .env file")
    else:
        print("⚠️  Could not find the placeholder line. Please update manually.")
    
    # Test the configuration
    print("\n🔍 Testing configuration...")
    os.environ["AZURE_OPENAI_KEY"] = api_key
    
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
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    update_env_file()
