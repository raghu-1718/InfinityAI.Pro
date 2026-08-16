import logging
from datetime import datetime
from typing import Dict, Optional
from io import StringIO

import pandas as pd
import aiohttp

logger = logging.getLogger(__name__)

class SymbolMapper:
    """
    Dynamic Symbol Mapping Service.
    Fetches the daily Master Scrip List from DhanHQ to ensure accurate mapping.
    """
    MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"

    def __init__(self):
        self.symbol_map: Dict[str, str] = {}  # Symbol -> Security ID
        self.id_map: Dict[int, str] = {}      # Security ID -> Symbol
        self.meta_map: Dict[int, Dict] = {}   # Security ID -> Metadata
        self.last_updated: Optional[datetime] = None
        self._load_fallback_mapping()

    def _load_fallback_mapping(self):
        """Load fallback mapping for critical symbols"""
        fallback = {
            # NSE & BSE Indices
            "NIFTY": "13", "NIFTY50": "13", "BANKNIFTY": "25", "FINNIFTY": "27",
            "MIDCPNIFTY": "442", "SENSEX": "51", "BSESN": "51", "BSE_SENSEX": "51",
            # MCX Commodities (Security IDs from Dhan MCX Master)
            "CRUDEOIL": "428416", "CRUDEOILM": "428424",
            "GOLD": "428219", "GOLDM": "428226", "GOLDPETAL": "428281",
            "SILVER": "428359", "SILVERM": "428366", "SILVERMIC": "428371",
            "NATURALGAS": "428431", "COPPER": "428439", "ZINC": "428456",
            "LEAD": "428463", "ALUMINIUM": "428478", "NICKEL": "428485"
        }
        self.symbol_map = fallback
        self.id_map = {int(v): k for k, v in fallback.items()}

    async def refresh(self, aiohttp_session: Optional[aiohttp.ClientSession] = None):
        """Downloads and parses the master scrip CSV from DhanHQ (optimized with connection pooling)"""
        if not aiohttp:
            logger.warning("aiohttp not available, using fallback symbol map")
            return

        try:
            logger.info("🔄 Refreshing Master Scrip List from DhanHQ...")

            # Use shared session if available, otherwise create temp session
            session = aiohttp_session
            should_close = False
            if session is None or session.closed:
                session = aiohttp.ClientSession()
                should_close = True

            try:
                async with session.get(self.MASTER_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to fetch CSV: {resp.status}")
                    csv_text = await resp.text()
            finally:
                if should_close:
                    await session.close()

            # Parse CSV
            df = pd.read_csv(
                StringIO(csv_text),
                usecols=['SEM_TRADING_SYMBOL', 'SEM_SMST_SECURITY_ID', 'SEM_EXM_EXCH_ID', 'SEM_SERIES', 'SEM_LOT_UNITS'],
                low_memory=False
            )

            # Filter for NSE Equity, Derivatives, MCX Commodities & BSE Indices
            df = df[df['SEM_EXM_EXCH_ID'].isin(['NSE', 'NSE_FNO', 'MCX', 'BSE', 'BSE_FNO'])].copy()

            # Prioritize NSE over BSE so NSE Security IDs take precedence for equities
            prio_map = {'NSE': 0, 'NSE_FNO': 1, 'MCX': 2, 'BSE': 3, 'BSE_FNO': 4}
            df['prio'] = df['SEM_EXM_EXCH_ID'].map(prio_map).fillna(9)
            df = df.sort_values('prio')

            # Remove duplicates before building maps to avoid "index must be unique" error
            df_symbols = df.drop_duplicates(subset=['SEM_TRADING_SYMBOL'], keep='first')
            df_sec_ids = df.drop_duplicates(subset=['SEM_SMST_SECURITY_ID'], keep='first')

            # Build Maps
            self.symbol_map = pd.Series(
                df_symbols.SEM_SMST_SECURITY_ID.astype(str).values,
                index=df_symbols.SEM_TRADING_SYMBOL
            ).to_dict()

            self.id_map = pd.Series(
                df_sec_ids.SEM_TRADING_SYMBOL.values,
                index=df_sec_ids.SEM_SMST_SECURITY_ID.astype(int)
            ).to_dict()

            # Handle duplicate security IDs by keeping first occurrence
            self.meta_map = df_sec_ids.set_index('SEM_SMST_SECURITY_ID')[['SEM_SERIES', 'SEM_LOT_UNITS']].to_dict('index')

            # Merge fallback critical symbols (MCX commodities use expiry-based names in CSV)
            fallback_critical = {
                "CRUDEOIL": "428416", "CRUDEOILM": "428424",
                "GOLD": "428219", "GOLDM": "428226", "GOLDPETAL": "428281",
                "SILVER": "428359", "SILVERM": "428366", "SILVERMIC": "428371",
                "NATURALGAS": "428431", "COPPER": "428439", "ZINC": "428456",
                "LEAD": "428463", "ALUMINIUM": "428478", "NICKEL": "428485",
                "NIFTY": "13", "NIFTY50": "13", "BANKNIFTY": "25", "FINNIFTY": "27",
                "MIDCPNIFTY": "442", "SENSEX": "51", "BSESN": "51", "BSE_SENSEX": "51"
            }
            for sym, sec_id in fallback_critical.items():
                if sym not in self.symbol_map:
                    self.symbol_map[sym] = sec_id
                    logger.info(f"📌 Added fallback mapping: {sym} -> {sec_id}")

            self.last_updated = datetime.now()
            logger.info(f"✅ Symbol Map Updated: {len(self.symbol_map)} symbols loaded (incl. fallback)")

        except Exception as e:
            logger.error(f"❌ Symbol Map Refresh Failed: {e}, reloading fallback")
            self._load_fallback_mapping()  # Restore fallback mappings on failure

    def get_id(self, symbol: str) -> Optional[str]:
        return self.symbol_map.get(symbol.upper())

    def get_symbol(self, sec_id: str) -> Optional[str]:
        try:
            return self.id_map.get(int(sec_id))
        except:
            return None

    def get_metadata(self, sec_id: str) -> Dict:
        try:
            return self.meta_map.get(int(sec_id), {})
        except:
            return {}
