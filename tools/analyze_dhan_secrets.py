from dhanhq import dhanhq
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credentials retrieved from Secret Manager
CLIENT_ID = "1101302170"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3Njg2NjQzNDAsImlhdCI6MTc2ODU3Nzk0MCwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.d7tffa3tVIlkKuOTbQHZDHDGLHv-VqNiQf6G63u7_6ehh4bpzpWJOPDhtQV0UtF7w4mg_uTHi9JhtGNdurZ5vA"

def analyze_dhan_access():
    logger.info("Starting DEEP Deep DhanHQ Analysis using Secret Manager credentials...")
    logger.info(f"Using Client ID: {CLIENT_ID}")
    
    try:
        dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
        
        # 1. Profile / Connectivity Check
        logger.info("\n--- 1. CONNECTIVITY CHECK ---")
        try:
            funds = dhan.get_fund_limits()
            logger.info("✅ Get Funds: SUCCESS")
            # logger.info(f"Funds Data: {funds}")
        except Exception as e:
            logger.error(f"❌ Get Funds: FAILED ({e})")
            
        # 2. Holdings Check (Portfolio Access)
        logger.info("\n--- 2. PORTFOLIO ACCESS CHECK ---")
        try:
            holdings = dhan.get_holdings()
            if isinstance(holdings, dict) and holdings.get('status') == 'failure':
                logger.error(f"❌ Get Holdings: FAILED - {holdings.get('remarks')}")
            else:
                logger.info("✅ Get Holdings: SUCCESS")
        except Exception as e:
            logger.error(f"❌ Get Holdings: EXCEPTION ({e})")

        # 3. Data API Check (Market Feed) - CRITICAL
        logger.info("\n--- 3. DATA API CHECK (CRITICAL) ---")
        try:
            # Test with NIFTY 50 (Index)
            # Exchange Segment: IDX_I (or NSE_IDX depending on library version/dhan conventions)
            # Security ID: 13
            logger.info("Attempting fetch for NIFTY 50 (Index)...")
            # Note: DhanHQ usually uses 'IDX_I' for indices in ohlc_data? Let's try.
            # Or standard NSE_IDX.
            quote_nifty = dhan.ohlc_data({'IDX_I': [13]})
            logger.info(f"Quote Result (NIFTY): {quote_nifty}")
            
            if isinstance(quote_nifty, dict) and quote_nifty.get('status') == 'failure':
                 logger.error("❌ Data API (NIFTY): FAILED.")
            else:
                 logger.info("✅ Data API (NIFTY): SUCCESS")
                 
        except Exception as e:
            logger.error(f"❌ Data API (NIFTY): EXCEPTION ({e})")

        # 4. Option Chain Check (Derivatives Data)
        logger.info("\n--- 4. OPTION CHAIN CHECK ---")
        try:
            # NIFTY Index (13)
            logger.info("Attempting Option Chain fetch for NIFTY...")
            chain = dhan.option_chain(13, 'IDX_I', '2026-01-22') # Future expiry
            logger.info(f"Option Chain Result type: {type(chain)}")
            if isinstance(chain, dict) and chain.get('status') == 'failure':
                logger.info(f"Chain Response: {chain}")
                logger.error("❌ Option Chain: FAILED - " + str(chain.get('remarks')))
            else:
                 # If it returns list, it's success (usually)
                 if isinstance(chain, list) and len(chain) > 0:
                     logger.info(f"✅ Option Chain: SUCCESS (Count: {len(chain)})")
                 elif isinstance(chain, dict) and 'data' in chain:
                     logger.info("✅ Option Chain: SUCCESS (Data wrapper present)")
                 else:
                     logger.warning(f"⚠️ Option Chain: UNKNOWN STATE ({chain})")
        except Exception as e:
            logger.error(f"❌ Option Chain: EXCEPTION ({e})")

    except Exception as e:
        logger.critical(f"Global Failure: {e}")

if __name__ == "__main__":
    analyze_dhan_access()
