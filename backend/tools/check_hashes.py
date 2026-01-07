
import hashlib

def hash_code(code: str) -> str:
    """Hash coupon code for secure comparison"""
    return hashlib.sha256(code.upper().strip().encode()).hexdigest()

codes = [
    "INFAI-FAM-DAD",
    "INFAI-FAM-MOM",
    "INFAI-FAM-SAI",
    "INFAI-FAM-1718"
]

print("--- Coupon Hash Check ---")
for c in codes:
    h = hash_code(c)
    print(f"Code: {c} -> Hash: {h}")
