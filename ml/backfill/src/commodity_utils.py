"""
Commodity Markets Utility - Trading Hours and Helpers
"""
import json
import os
from datetime import datetime, time
from typing import Dict, List, Optional

# Load commodity configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'commodity_markets_config.json')

def load_commodity_config() -> Dict:
    """Load commodity markets configuration."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Commodity config not found at {CONFIG_PATH}")
        return {"mcx_commodities": [], "enabled": False}

def is_commodity_market_open(check_time: Optional[datetime] = None) -> bool:
    """
    Check if MCX commodity markets are currently open.
    MCX trading hours: 9:00 AM to 11:30 PM IST
    """
    if check_time is None:
        check_time = datetime.now()
    
    current_time = check_time.time()
    
    # MCX trading hours
    market_open = time(9, 0)  # 9:00 AM
    market_close = time(23, 30)  # 11:30 PM
    
    # Check if current time is within trading hours
    return market_open <= current_time <= market_close

def get_active_commodities() -> List[Dict]:
    """Get list of enabled commodity instruments."""
    config = load_commodity_config()
    
    if not config.get('enabled', False):
        return []
    
    return [c for c in config.get('mcx_commodities', []) if c.get('enabled', True)]

def get_commodity_by_symbol(symbol: str) -> Optional[Dict]:
    """Get commodity configuration by symbol."""
    commodities = get_active_commodities()
    
    for commodity in commodities:
        if commodity['symbol'] == symbol.upper():
            return commodity
    
    return None

def get_commodity_trading_window() -> Dict:
    """Get current MCX trading window status."""
    now = datetime.now()
    is_open = is_commodity_market_open(now)
    
    # Calculate time until market open/close
    current_time = now.time()
    market_open = time(9, 0)
    market_close = time(23, 30)
    
    if is_open:
        # Market is open - calculate time until close
        close_datetime = datetime.combine(now.date(), market_close)
        time_remaining = (close_datetime - now).total_seconds() / 60  # minutes
        
        return {
            "status": "OPEN",
            "current_time": now.strftime("%H:%M:%S"),
            "market_open": "09:00",
            "market_close": "23:30",
            "minutes_until_close": int(time_remaining),
            "can_trade": True
        }
    else:
        # Market is closed - calculate time until open
        if current_time < market_open:
            # Before market open today
            open_datetime = datetime.combine(now.date(), market_open)
        else:
            # After market close - next open is tomorrow
            from datetime import timedelta
            tomorrow = now.date() + timedelta(days=1)
            open_datetime = datetime.combine(tomorrow, market_open)
        
        time_until_open = (open_datetime - now).total_seconds() / 60  # minutes
        
        return {
            "status": "CLOSED",
            "current_time": now.strftime("%H:%M:%S"),
            "market_open": "09:00",
            "market_close": "23:30",
            "minutes_until_open": int(time_until_open),
            "can_trade": False
        }

def format_commodity_signal(commodity: Dict, signal_data: Dict) -> Dict:
    """Format a trading signal for commodity markets."""
    return {
        "symbol": commodity['symbol'],
        "display_name": commodity['display_name'],
        "security_id": commodity['security_id'],
        "exchange_segment": commodity['exchange_segment'],
        "lot_size": commodity['lot_size'],
        "contract_type": commodity['contract_type'],
        "signal": signal_data,
        "market_status": get_commodity_trading_window(),
        "timestamp": datetime.utcnow().isoformat()
    }
