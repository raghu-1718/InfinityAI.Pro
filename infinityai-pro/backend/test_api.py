#!/usr/bin/env python3

import requests
import json

def test_chatbot_api():
    url = 'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat'
    
    payload = {
        "message": "Hello, how are you?",
        "user_id": "test123",
        "voice_input": False
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"Testing URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {headers}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print("Could not parse response as JSON")
        else:
            print(f"❌ FAILED with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")

def test_health_endpoint():
    url = 'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health'
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Health check - Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        return response.status_code == 200
    except:
        print("❌ Health endpoint failed")
        return False

if __name__ == "__main__":
    print("=== Testing InfinityAI.Pro Backend API ===\n")
    
    # Test health first
    print("1. Testing health endpoint...")
    if test_health_endpoint():
        print("\n2. Testing chatbot endpoint...")
        test_chatbot_api()
    else:
        print("Backend seems to be down, skipping chatbot test")