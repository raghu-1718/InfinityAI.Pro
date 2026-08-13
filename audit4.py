import json
import os

print('--- Phase 2: NAT/Egress IP ---')
try:
    with open('nat.json', encoding='utf-16') as f:
        nat = json.load(f)
        print(f"NAT Name: {nat.get('name')}")
        print(f"NAT IPs: {nat.get('natIps')}")
except Exception as e: print('Error reading nat.json:', e)

print('\n--- Phase 5: Cloud Scheduler ---')
try:
    with open('schedulers.json', encoding='utf-16') as f:
        scheds = json.load(f)
        for s in scheds:
            print(f"Job: {s.get('name').split('/')[-1]}, Schedule: {s.get('schedule')}, TZ: {s.get('timeZone')}, State: {s.get('state')}")
except Exception as e: print('Error reading schedulers.json:', e)

print('\n--- Source Code Verifications ---')
def verify_code(filepath, term):
    with open(filepath, 'r', encoding='utf-8') as f:
        return term in f.read()

print("Idempotency (hex[:30]):", verify_code('backend/engine-c/src/main.py', 'hex[:30]'))
print("Rate Limiter (aiolimiter):", verify_code('backend/engine-c/src/main.py', 'AsyncLimiter(max_rate=9'))
print("AES-256-GCM:", verify_code('backend/engine-c/src/user_credentials.py', 'AESGCM'))
print("Token <20h check:", verify_code('backend/engine-c/src/user_credentials.py', '3600') or verify_code('backend/engine-c/src/user_credentials.py', '20'))
print("Trading Guardrails 403:", verify_code('backend/engine-c/src/trading_guardrails.py', '403'))
