import requests

r = requests.post(
    'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat', 
    json={'message': 'test', 'user_id': 'test', 'voice_input': False}
)

print(f'Method: {r.request.method}')
print(f'Status: {r.status_code}') 
print(f'Allow header: {r.headers.get("allow", "none")}')
print(f'Response: {r.text}')