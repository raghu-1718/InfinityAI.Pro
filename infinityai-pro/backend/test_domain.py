import requests

# Test the custom domain
urls = [
    'https://api.infinityai.pro/api/chatbot/chat',
    'http://api.infinityai.pro/api/chatbot/chat',
    'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat'
]

payload = {'message': 'test', 'user_id': 'test', 'voice_input': False}

for url in urls:
    try:
        print(f"\nTesting URL: {url}")
        r = requests.post(url, json=payload, timeout=10, allow_redirects=False)
        print(f'Status: {r.status_code}')
        print(f'Method sent: {r.request.method}') 
        print(f'Allow header: {r.headers.get("allow", "none")}')
        if r.status_code in [301, 302, 307, 308]:
            print(f'Redirect to: {r.headers.get("location", "none")}')
    except Exception as e:
        print(f'Error: {e}')