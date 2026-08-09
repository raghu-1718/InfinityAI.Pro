from dhanhq import dhanhq
print("MARKET:", dhanhq.MARKET)
print("LIMIT:", dhanhq.LIMIT)
print("SL:", getattr(dhanhq, 'SL', 'missing'))
print("SLM:", getattr(dhanhq, 'SLM', 'missing'))
print("STOP_LOSS:", getattr(dhanhq, 'STOP_LOSS', 'missing'))
