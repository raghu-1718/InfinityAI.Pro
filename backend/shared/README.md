# backend/shared/README.md

## Backend Shared Utilities

**Purpose**: Common Python utilities, API clients, models, and configuration shared across all three backend engines.

**Technology**: Python, Pydantic, Python requests

### Directory Structure

```
shared/
├── clients/
│   ├── firestore_client.py    # Firestore singleton, common operations
│   ├── gemini_client.py       # Google Gemini API wrapper
│   ├── dhan_client.py         # Dhan broker API wrapper
│   ├── secret_manager.py      # Google Cloud Secret Manager integration
│   └── __init__.py
├── utils/
│   ├── logger.py              # Structured logging configuration
│   ├── validators.py          # Common validation functions
│   ├── decorators.py          # Retry, rate limit, timing decorators
│   ├── exceptions.py          # Custom exception classes
│   └── __init__.py
├── models/
│   ├── market_data.py         # Market data schemas (Pydantic)
│   ├── signals.py             # Trading signal schemas
│   ├── orders.py              # Order and execution schemas
│   ├── users.py               # User and authentication schemas
│   └── __init__.py
├── config/
│   ├── settings.py            # Global configuration (env variables)
│   ├── constants.py           # Application constants (symbols, exchanges)
│   ├── trading_rules.py       # Risk management rules
│   └── __init__.py
├── setup.py                   # Installable Python package
└── README.md
```

### Usage in Engines

```python
# In any engine:
from backend.shared.clients import FirestoreClient, GeminiClient
from backend.shared.utils import get_logger, validate_symbol
from backend.shared.models import MarketData, TradingSignal
from backend.shared.config import get_settings

logger = get_logger(__name__)
settings = get_settings()
firestore = FirestoreClient()

# Validate input
if not validate_symbol(symbol):
    raise ValueError(f"Invalid symbol: {symbol}")

# Query Firestore
market_data = firestore.get_collection("market_data").document(symbol).get()

# Use shared models
data = MarketData.parse_obj(market_data.to_dict())
```

### Key Components

#### Firestore Client
```python
from backend.shared.clients import FirestoreClient

fc = FirestoreClient()
# Read
doc = fc.get_document("market_data", "NIFTY")
# Write
fc.set_document("market_data", "NIFTY", {"price": 19200, ...})
# Batch
fc.batch_set(collection, [{id, data}, ...])
```

#### Secret Manager
```python
from backend.shared.clients import get_secret

dhan_key = get_secret("dhan-api-key")  # Retrieves from GCP Secret Manager
```

#### Logging
```python
from backend.shared.utils import get_logger

logger = get_logger(__name__)
logger.info("Market data update", extra={"symbol": "NIFTY", "price": 19200})
# Output: structured JSON logs to Cloud Logging
```

#### Models
```python
from backend.shared.models import TradingSignal, Order

signal = TradingSignal(
    symbol="NIFTY",
    action="BUY",
    confidence=0.92,
    price_target=19250.50
)

order = Order(
    user_id="user123",
    symbol="NIFTY",
    quantity=1,
    price=19200.00,
    order_type="LIMIT"
)
```

### Installation

```bash
# Install as editable package in each engine
cd backend/engine-core
pip install -e ../shared

cd ../engine-analytics
pip install -e ../shared

cd ../engine-execution
pip install -e ../shared
```

### Configuration

Global settings loaded from environment variables or `.env` file:

```python
from backend.shared.config import get_settings

settings = get_settings()
print(settings.firestore_project)  # gen-lang-client-0779271931
print(settings.debug)  # False in production
print(settings.cors_origins)  # Parsed from env
```

### Security

- All sensitive values (API keys, secrets) retrieved from Google Cloud Secret Manager
- Credentials never logged or exposed in error messages
- JWT tokens validated for all internal API calls
- CORS origins configurable per environment

### Dependencies

```
firebase-admin>=6.0.0
google-cloud-secret-manager>=2.0.0
google-cloud-firestore>=2.0.0
pydantic>=2.0.0
requests>=2.28.0
python-dotenv>=0.21.0
```

### Common Patterns

#### Error Handling
```python
from backend.shared.utils.exceptions import InternalServiceError

try:
    result = firestore.get_document(...)
except Exception as e:
    logger.error("Firestore error", exc_info=True)
    raise InternalServiceError("Failed to fetch data") from e
```

#### Retry Logic
```python
from backend.shared.utils.decorators import retry_with_backoff

@retry_with_backoff(max_retries=3)
def call_external_api():
    return requests.get("https://...")
```

#### Rate Limiting
```python
from backend.shared.utils.decorators import rate_limit

@rate_limit(calls=100, period=60)  # 100 calls per minute
async def get_market_data(symbol: str):
    return await firestore.get_document("market_data", symbol)
```

### Contributing

When adding new shared utilities:
1. Add to appropriate module (clients/, utils/, models/, config/)
2. Update docstrings with usage examples
3. Add unit tests to `tests/`
4. Update this README with new patterns
5. Ensure backward compatibility with existing engines
