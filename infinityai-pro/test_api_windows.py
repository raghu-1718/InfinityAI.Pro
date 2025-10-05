#!/usr/bin/env python3
"""
Simple API test for Windows
"""

import requests
import json

def test_chatbot():
    print("🤖 Testing InfinityAI.Pro Chatbot...")
    
    # Test data
    payload = {
        "message": "Scan NIFTY with 50 thousand",
        "user_id": "raghu_test",
        "voice_input": False
    }
    
    try:
        response = requests.post(
            "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat",
            json=payload,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"Bot Response: {data['data']['response']}")
            print(f"Timestamp: {data['timestamp']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_health():
    print("\n💗 Testing API Health...")
    
    try:
        response = requests.get(
            "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API is healthy!")
            print(f"Platform: {data['platform']}")
            print(f"Version: {data['version']}")
            print(f"Services: {', '.join(data['services'].keys())}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_frontend():
    print("\n🌐 Testing Frontend...")
    
    frontend_url = "https://infinity-ai-9utba60h7-infinityaipro.vercel.app"
    
    try:
        response = requests.get(frontend_url, timeout=15)
        
        if response.status_code == 200:
            has_title = "InfinityAI" in response.text
            print("✅ Frontend is accessible!")
            print(f"URL: {frontend_url}")
            print(f"Contains InfinityAI title: {has_title}")
            
            if has_title:
                print("🎉 Your app is ready to use!")
            else:
                print("⚠️ Frontend loaded but may need refresh")
        else:
            print(f"❌ Frontend error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend error: {e}")

if __name__ == "__main__":
    print("🚀 InfinityAI.Pro Quick Test")
    print("=" * 40)
    
    test_health()
    test_chatbot()  
    test_frontend()
    
    print("\n" + "=" * 40)
    print("🎯 Access your application at:")
    print("📱 https://infinity-ai-9utba60h7-infinityaipro.vercel.app")
    print("🔗 https://infinityai.pro (if DNS is ready)")
    print("🛠️ API: https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io")