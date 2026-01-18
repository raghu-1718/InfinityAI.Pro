"""
DhanHQ Option Chain Data Fetcher
Fetches complete option chain data for NSE F&O instruments
"""
import requests
import pandas as pd
from datetime import datetime

class DhanOptionChainFetcher:
    """
    Fetch option chain data from DhanHQ API
    """
    
    def __init__(self, access_token, client_id, base_url="https://api.dhan.co"):
        self.access_token = access_token
        self.client_id = client_id
        self.base_url = base_url
        self.headers = {
            "access-token": access_token,
            "Content-Type": "application/json"
        }
    
    def fetch_option_chain(self, security_id, exchange_segment="NSE_FNO"):
        """
        Fetch complete option chain for a security
        
        Args:
            security_id: Underlying security ID (e.g., NIFTY, BANKNIFTY)
            exchange_segment: Exchange segment (NSE_FNO, BSE_FNO)
        
        Returns:
            DataFrame with option chain data
        """
        endpoint = f"{self.base_url}/v2/optionchain"
        
        params = {
            "security_id": security_id,
            "exchange_segment": exchange_segment
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                print(f"[OK] Fetched option chain: {len(df)} contracts")
                return df
            else:
                print(f"[ERROR] API returned {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to fetch option chain: {str(e)}")
            return None
    
    def parse_option_chain(self, df):
        """
        Parse and structure option chain data
        """
        if df is None or df.empty:
            return None
        
        # Separate calls and puts
        calls = df[df['option_type'] == 'CALL'].copy()
        puts = df[df['option_type'] == 'PUT'].copy()
        
        # Get unique strike prices
        strikes = sorted(df['strike_price'].unique())
        
        # Create structured chain
        chain = []
        for strike in strikes:
            call_data = calls[calls['strike_price'] == strike]
            put_data = puts[puts['strike_price'] == strike]
            
            chain.append({
                'strike': strike,
                'call_oi': call_data['open_interest'].sum() if not call_data.empty else 0,
                'call_volume': call_data['volume'].sum() if not call_data.empty else 0,
                'call_ltp': call_data['ltp'].iloc[0] if not call_data.empty else 0,
                'call_iv': call_data.get('implied_volatility', pd.Series([0])).iloc[0] if not call_data.empty else 0,
                'put_oi': put_data['open_interest'].sum() if not put_data.empty else 0,
                'put_volume': put_data['volume'].sum() if not put_data.empty else 0,
                'put_ltp': put_data['ltp'].iloc[0] if not put_data.empty else 0,
                'put_iv': put_data.get('implied_volatility', pd.Series([0])).iloc[0] if not put_data.empty else 0
            })
        
        return pd.DataFrame(chain)
    
    def calculate_pcr(self, chain_df):
        """
        Calculate Put-Call Ratio
        """
        total_put_oi = chain_df['put_oi'].sum()
        total_call_oi = chain_df['call_oi'].sum()
        
        if total_call_oi > 0:
            pcr = total_put_oi / total_call_oi
            return round(pcr, 2)
        return 0
    
    def identify_atm_strike(self, chain_df, spot_price):
        """
        Identify ATM (At-The-Money) strike
        """
        chain_df['distance'] = abs(chain_df['strike'] - spot_price)
        atm = chain_df.loc[chain_df['distance'].idxmin(), 'strike']
        return atm
    
    def get_max_pain(self, chain_df):
        """
        Calculate Max Pain strike
        Max Pain = Strike where option holders lose maximum money
        """
        max_pain_values = []
        
        for strike in chain_df['strike']:
            # Calculate total value lost by option holders
            call_loss = chain_df[chain_df['strike'] < strike]['call_oi'].sum() * \
                       (strike - chain_df[chain_df['strike'] < strike]['strike']).sum()
            put_loss = chain_df[chain_df['strike'] > strike]['put_oi'].sum() * \
                      (chain_df[chain_df['strike'] > strike]['strike'] - strike).sum()
            
            total_loss = call_loss + put_loss
            max_pain_values.append({'strike': strike, 'total_loss': total_loss})
        
        max_pain_df = pd.DataFrame(max_pain_values)
        if not max_pain_df.empty:
            max_pain_strike = max_pain_df.loc[max_pain_df['total_loss'].idxmax(), 'strike']
            return max_pain_strike
        return None

# Demo with sandbox credentials
if __name__ == "__main__":
    print("=" * 80)
    print("  DHANHQ OPTION CHAIN FETCHER - DEMO")
    print("=" * 80)
    
    # Sandbox credentials
    SANDBOX_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"
    SANDBOX_CLIENT_ID = "2508215064"
    SANDBOX_URL = "https://sandbox.dhan.co"
    
    fetcher = DhanOptionChainFetcher(SANDBOX_TOKEN, SANDBOX_CLIENT_ID, SANDBOX_URL)
    
    print("\n[INFO] Option Chain API integration ready")
    print("[INFO] Note: Sandbox may have limited option chain data")
    print("[INFO] For production: Use production API credentials")
    
    print("\n[DEMO] Structure ready for:")
    print("  - Fetch complete option chain")
    print("  - Calculate Put-Call Ratio (PCR)")
    print("  - Identify ATM strike")
    print("  - Calculate Max Pain")
    print("  - Analyze Open Interest")
    
    print("\n" + "=" * 80)
    print("  OPTION CHAIN FETCHER READY")
    print("=" * 80)
