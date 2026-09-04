import logging, json, time
from datetime import datetime

def setup_logger(name="EngineC", level="INFO"):
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, level.upper())
    )
    return logging.getLogger(name)

def retry(func, retries=3, delay=1):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise e

def pretty_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)
