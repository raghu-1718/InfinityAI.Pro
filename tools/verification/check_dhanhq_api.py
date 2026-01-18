"""
Quick test to see what methods dhanhq library actually has
"""
from dhanhq import dhanhq, marketfeed

# Check main dhanhq class
print("=== dhanhq class methods ===")
client = dhanhq("test", "test")
methods = [m for m in dir(client) if not m.startswith('_')]
for m in methods:
    print(f"  - {m}")

print("\n=== marketfeed.DhanFeed class methods ===")
try:
    feed = marketfeed.DhanFeed("test", "test", instruments=[(1, "NIFTY")])
    methods = [m for m in dir(feed) if not m.startswith('_')]
    for m in methods:
        print(f"  - {m}")
except Exception as e:
    print(f"  Error: {e}")
