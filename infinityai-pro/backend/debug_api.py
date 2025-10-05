#!/usr/bin/env python3

import requests
import json
from requests.adapters import HTTPAdapter
import urllib3

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
requests.packages.urllib3.add_stderr_logger()

def test_chatbot_with_manual_post():
    url = 'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat'
    
    payload = {
        "message": "Hello, how are you?",
        "user_id": "test123",
        "voice_input": False
    }
    
    print(f"Testing URL: {url}")
    print(f"Method: POST")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Test with different approaches
    approaches = [
        ("Using requests.post with json=", lambda: requests.post(url, json=payload, timeout=10)),
        ("Using requests.post with data= and headers=", lambda: requests.post(
            url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'}, 
            timeout=10
        )),
        ("Using requests.request with POST method", lambda: requests.request(
            'POST', 
            url, 
            json=payload, 
            timeout=10
        )),
    ]
    
    for approach_name, make_request in approaches:
        print(f"\n--- Testing: {approach_name} ---")
        try:
            response = make_request()
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            print(f"Request Method: {response.request.method}")
            print(f"Request URL: {response.request.url}")
            print(f"Request Headers: {dict(response.request.headers)}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                return True
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=== Debugging InfinityAI.Pro Backend API ===")
    test_chatbot_with_manual_post()