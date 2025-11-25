#!/usr/bin/env python3
"""
Strategy loader copied into `Iaminfinity/strategies` so Engine A/B can import locally.
"""

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Directory where strategies (Python files) are stored
STRATEGY_DIR = Path(__file__).parent

class StrategyLoader:
    def __init__(self, strategy_dir: Optional[Path] = None):
        self.strategy_dir = strategy_dir or STRATEGY_DIR
        self.loaded_strategies: Dict[str, Any] = {}
        if str(self.strategy_dir) not in sys.path:
            sys.path.insert(0, str(self.strategy_dir))
        logger.info(f"StrategyLoader initialized with directory: {self.strategy_dir}")

    def list_strategies(self) -> List[str]:
        strategies = []
        for file in self.strategy_dir.glob("*.py"):
            if file.stem not in ["__init__", "strategy_loader"]:
                strategies.append(file.stem)
        return sorted(strategies)

    def load_strategy(self, name: str, reload: bool = False) -> Optional[Any]:
        try:
            if name in self.loaded_strategies and not reload:
                return self.loaded_strategies[name]
            if reload and name in sys.modules:
                strategy = importlib.reload(sys.modules[name])
            else:
                strategy = importlib.import_module(name)
            if not hasattr(strategy, 'run'):
                logger.warning(f"Strategy '{name}' missing 'run' method")
            self.loaded_strategies[name] = strategy
            return strategy
        except ModuleNotFoundError:
            logger.error(f"Strategy module '{name}' not found in {self.strategy_dir}")
            return None
        except Exception as e:
            logger.error(f"Error loading strategy '{name}': {e}")
            return None

    def execute_strategy(self, name: str, data: Dict[str, Any], method: str = "run", **kwargs) -> Optional[Dict[str, Any]]:
        strategy = self.load_strategy(name)
        if not strategy:
            return None
        if not hasattr(strategy, method):
            return None
        method_func = getattr(strategy, method)
        return method_func(data, **kwargs)

_strategy_loader = None

def get_strategy_loader() -> StrategyLoader:
    global _strategy_loader
    if _strategy_loader is None:
        _strategy_loader = StrategyLoader()
    return _strategy_loader

def list_strategies() -> List[str]:
    return get_strategy_loader().list_strategies()

def load_strategy(name: str) -> Optional[Any]:
    return get_strategy_loader().load_strategy(name)

def execute_strategy(name: str, data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    return get_strategy_loader().execute_strategy(name, data, **kwargs)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    loader = StrategyLoader()
    print("Available strategies:", loader.list_strategies())