import os
import json
from typing import Any, Dict

def load_config(filename: str) -> Dict[str, Any]:
    """Load a JSON config file from the config directory."""
    config_path = os.path.join(os.path.dirname(__file__), '../config', filename)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Example usage:
# config = load_config('test_payload.json')
