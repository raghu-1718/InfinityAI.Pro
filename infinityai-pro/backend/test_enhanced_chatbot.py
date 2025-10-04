#!/usr/bin/env python3
"""
Test Enhanced Chatbot API - InfinityAI.Pro
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
API_BASE_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
CHATBOT_ENDPOINT = f"{API_BASE_URL}/api/chatbot/chat"
STATUS_ENDPOINT = f"{API_BASE_URL}/api/chatbot/chatbot-status"
COMMANDS_ENDPOINT = f"{API_BASE_URL}/api/chatbot/command-examples"

def test_chatbot_command(message: str, user_id: str = "test_user") -> Dict[str, Any]:
    """Test a chatbot command"""
    
    print(f"\n🤖 Testing Command: '{message}'")
    print("=" * 60)
    
    try:
        payload = {
            "message": message,
            "user_id": user_id
        }
        
        response = requests.post(
            CHATBOT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('success', False)}")
            print(f"📝 Response: {result.get('message', 'No message')}")
            print(f"🔄 Type: {result.get('type', 'unknown')}")
            
            if result.get('data'):
                print(f"📊 Data: {json.dumps(result['data'], indent=2)}")
            
            return result
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": f"HTTP {response.status_code}", "response": response.text}
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}

def get_chatbot_status() -> Dict[str, Any]:
    """Get chatbot status"""
    
    print("\n🔍 Getting Chatbot Status...")
    print("=" * 40)
    
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status: {status.get('status', 'unknown')}")
            print(f"📊 Active Sessions: {status.get('statistics', {}).get('active_sessions', 0)}")
            print(f"🎯 Capabilities: {len(status.get('capabilities', []))} features")
            return status
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}

def get_command_examples() -> Dict[str, Any]:
    """Get supported command examples"""
    
    print("\n📚 Getting Command Examples...")
    print("=" * 40)
    
    try:
        response = requests.get(COMMANDS_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            examples = response.json()
            print(f"✅ Trading Commands: {len(examples.get('command_examples', {}).get('trading_commands', []))}")
            print(f"📊 Analysis Commands: {len(examples.get('command_examples', {}).get('analysis_commands', []))}")
            print(f"🎯 Supported Symbols: {len(examples.get('supported_symbols', []))}")
            return examples
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}

def main():
    """Main testing function"""
    
    print("🚀 InfinityAI.Pro - Enhanced Chatbot Testing")
    print("=" * 60)
    
    # Get chatbot status first
    status = get_chatbot_status()
    time.sleep(1)
    
    # Get command examples
    examples = get_command_examples()
    time.sleep(1)
    
    # Test various commands
    test_commands = [
        "help",
        "integrate broker token abc123xyz",
        "start trading NIFTY with 50000 capital", 
        "show portfolio",
        "scan market for momentum opportunities",
        "stop trading",
        "get risk analysis",
        "what's the sentiment for RELIANCE?",
        "analyze BANKNIFTY for swing trading",
        "unknown command test"
    ]
    
    print("\n🧪 Testing Enhanced Chatbot Commands...")
    print("=" * 60)
    
    results = []
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n[{i}/{len(test_commands)}] Testing...")
        result = test_chatbot_command(command)
        results.append({"command": command, "result": result})
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 40)
    successful_tests = sum(1 for r in results if r['result'].get('success', False) or 'error' not in r['result'])
    print(f"✅ Successful Tests: {successful_tests}/{len(results)}")
    print(f"❌ Failed Tests: {len(results) - successful_tests}/{len(results)}")
    
    # Show interesting responses
    print("\n🎯 Key Responses:")
    print("-" * 30)
    
    for result in results[:3]:  # Show first 3 responses
        if result['result'].get('message'):
            print(f"Command: {result['command'][:30]}...")
            print(f"Response: {result['result']['message'][:100]}...\n")
    
    print("🎉 Enhanced Chatbot Testing Complete!")

if __name__ == "__main__":
    main()