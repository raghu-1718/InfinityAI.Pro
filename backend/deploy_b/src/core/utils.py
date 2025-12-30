import asyncio, datetime, json, random, logging, os
logger = logging.getLogger("utils")

def utc_now() -> datetime.datetime:
    return datetime.datetime.utcnow()

def utc_now_str() -> str:
    return utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")

async def async_retry(fn, retries=3, delay=1.0, backoff=1.5):
    exc = None
    for i in range(retries):
        try:
            return await fn()
        except Exception as e:
            exc = e
            logger.warning(f"Retry {i+1}/{retries}: {e}")
            await asyncio.sleep(delay)
            delay *= backoff
    raise exc

def safe_json(obj) -> str:
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return "{}"

def env(name: str, default: str) -> str:
    return os.getenv(name, default)
