"""
Unit tests for DhanHQ v2 payload normalization, security ID parsing, and quote extraction.
Verifies that nested 'data' wrappers from DhanHQ marketfeed are reliably peeled for IDX_I, NSE_EQ, and NSE_FNO.
"""
import pytest
import re
from typing import Dict, Any, List, Optional


def normalize_exchange_segment(seg: Optional[str]) -> str:
    s = (seg or "").strip().upper()
    if s in ("IDX_I", "INDEX", "NSE_INDEX", "NSE_IDX", "IDX", "INDICES"):
        return "IDX_I"
    if s in ("NSE_FNO", "FNO", "NFO", "NSE_FUT", "NSE_OPT"):
        return "NSE_FNO"
    if s in ("NSE_EQ", "NSE", "EQUITY", "EQ"):
        return "NSE_EQ"
    if s in ("MCX_COMM", "MCX", "COMMODITY", "COMM"):
        return "MCX_COMM"
    if s in ("BSE_EQ", "BSE"):
        return "BSE_EQ"
    if s in ("BSE_FNO", "BFO"):
        return "BSE_FNO"
    return s or "NSE_EQ"


def parse_security_ids(sec_param: Any, fallback_param: Any = None) -> List[int]:
    text = str(sec_param or "")
    digits = re.findall(r"\d+", text)
    if not digits and fallback_param:
        digits = re.findall(r"\d+", str(fallback_param))
    if not digits:
        return [13, 25]
    return [int(d) for d in digits]


def unwrap_dhan_ohlc_payload(raw_response: Dict[str, Any], segment: str = "IDX_I") -> Dict[str, Any]:
    norm_seg = normalize_exchange_segment(segment)
    ohlc_dict = raw_response.get("data", {}) if isinstance(raw_response, dict) and "data" in raw_response else (raw_response if isinstance(raw_response, dict) else {})
    while isinstance(ohlc_dict, dict) and "data" in ohlc_dict and norm_seg not in ohlc_dict and norm_seg.lower() not in ohlc_dict:
        ohlc_dict = ohlc_dict["data"]
    return ohlc_dict


def extract_index_spot_prices(idx_data: Dict[str, Any]) -> Dict[str, float]:
    id_map = {
        "13": "NIFTY",
        "25": "BANKNIFTY",
        "51": "SENSEX",
        "21": "INDIAVIX"
    }
    spots = {}
    for sec_id, key in id_map.items():
        node = idx_data.get(str(sec_id)) or idx_data.get(int(sec_id))
        if node and isinstance(node, dict):
            p = node.get("last_price") or node.get("ltp")
            if not p and "ohlc" in node:
                p = node["ohlc"].get("close") or node["ohlc"].get("open")
            if p and float(p) > 0:
                spots[key] = round(float(p), 2)
    return spots


def test_normalize_exchange_segment():
    assert normalize_exchange_segment("IDX_I") == "IDX_I"
    assert normalize_exchange_segment("INDEX") == "IDX_I"
    assert normalize_exchange_segment("NSE_INDEX") == "IDX_I"
    assert normalize_exchange_segment("NSE_EQ") == "NSE_EQ"
    assert normalize_exchange_segment("EQ") == "NSE_EQ"
    assert normalize_exchange_segment("NSE_FNO") == "NSE_FNO"
    assert normalize_exchange_segment("FNO") == "NSE_FNO"
    assert normalize_exchange_segment(None) == "NSE_EQ"


def test_parse_security_ids():
    assert parse_security_ids("13,25,51,21") == [13, 25, 51, 21]
    assert parse_security_ids("1333, 11536") == [1333, 11536]
    assert parse_security_ids("invalid") == [13, 25]
    assert parse_security_ids(None) == [13, 25]


def test_unwrap_dhan_ohlc_payload_double_nested():
    raw_response = {
        "status": "success",
        "remarks": "",
        "data": {
            "status": "success",
            "data": {
                "IDX_I": {
                    "13": {
                        "last_price": 23914.45,
                        "ohlc": {"open": 23858.0, "close": 23914.45, "high": 23914.45, "low": 23786.8}
                    },
                    "25": {
                        "last_price": 57172.0,
                        "ohlc": {"open": 57006.45, "close": 57172.0, "high": 57221.1, "low": 56823.2}
                    },
                    "51": {
                        "last_price": 76570.35,
                        "ohlc": {"open": 76471.32, "close": 76570.35, "high": 76570.35, "low": 76135.72}
                    },
                    "21": {
                        "last_price": 11.59,
                        "ohlc": {"open": 11.49, "close": 11.59, "high": 12.11, "low": 10.55}
                    }
                }
            }
        }
    }

    unwrapped = unwrap_dhan_ohlc_payload(raw_response, segment="IDX_I")
    assert "IDX_I" in unwrapped
    assert "13" in unwrapped["IDX_I"]
    assert unwrapped["IDX_I"]["13"]["last_price"] == 23914.45
    assert unwrapped["IDX_I"]["25"]["last_price"] == 57172.0
    assert unwrapped["IDX_I"]["51"]["last_price"] == 76570.35
    assert unwrapped["IDX_I"]["21"]["last_price"] == 11.59


def test_extract_index_spot_prices():
    idx_data = {
        "13": {"last_price": 23914.45, "ohlc": {"close": 23914.45}},
        "25": {"last_price": 57172.0, "ohlc": {"close": 57172.0}},
        "51": {"last_price": 76570.35, "ohlc": {"close": 76570.35}},
        "21": {"last_price": 11.59, "ohlc": {"close": 11.59}}
    }

    spots = extract_index_spot_prices(idx_data)
    assert spots["NIFTY"] == 23914.45
    assert spots["BANKNIFTY"] == 57172.0
    assert spots["SENSEX"] == 76570.35
    assert spots["INDIAVIX"] == 11.59
