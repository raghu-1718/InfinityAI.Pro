#!/usr/bin/env python3
"""Check dhanhq API method signatures"""
from dhanhq import dhanhq
import inspect

client = dhanhq('test', 'test')

print("=== quote_data ===")
print(inspect.signature(client.quote_data))

print("\n=== intraday_minute_data ===")
print(inspect.signature(client.intraday_minute_data))

print("\n=== historical_daily_data ===")
try:
    print(inspect.signature(client.historical_daily_data))
except AttributeError:
    print("Method not found")

print("\n=== option_chain ===")
print(inspect.signature(client.option_chain))

print("\n=== ohlc_data ===")
print(inspect.signature(client.ohlc_data))

print("\n=== All methods ===")
methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
for m in methods:
    print(f"  - {m}")
