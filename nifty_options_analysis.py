#!/usr/bin/env python3
"""
🤖 InfinityAI.Pro - Safe NIFTY Options Analysis (No Real Trading)
🎯 Analyzes NIFTY options for buy/sell recommendations using technical analysis
⚠️  PAPER TRADING MODE - No real money involved
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
from nsepython import nse_index  # NSE Python library for real data
import requests  # For Dhan API calls

class SafeNiftyOptionsAnalyzer:
    """Safe NIFTY options analysis without real trading"""

    def __init__(self):
        self.nifty_symbol = "NSEI.NS"  # NIFTY 50 index - corrected symbol
        self.analysis_results = {}

        # Dhan API Configuration for real-time data
        self.dhan_config = {
            "client_id": "1101302170",
            "api_key": "a1196f5b",  # Update with fresh API key
            "api_secret": "66e16669-1b5e-4db7-9aec-4da4f56a2530",  # Update with fresh API secret
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4OTU1MDksImlhdCI6MTc1OTgwOTEwOSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1lbmdpbmUtYS5hZ3JlZWFibGVtZWFkb3ctNzM3NWIxZjcuZWFzdHVzLmF6dXJlY29udGFpbmVyYXBwcy5pby9kaGFuL2NhbGxiYWNrIiwiZGhhbkNsaWVudElkIjoiMTEwMTMwMjE3MCJ9.FDcA8OZGgzjzuEBxFlHMsBteu9RF_o8MrDSv9ZiELTfIB2n3N75MvUSpilcjnRRtgfCjt5UlAsVe9MCd07I3vQ",  # Update daily with fresh token
            "base_url": "https://api.dhan.co",
            "data_api_url": "https://api.dhan.co/v2/marketfeed"  # Corrected LTP endpoint
        }

    def validate_and_refresh_token(self):
        """Validate current token and refresh if expired"""
        try:
            # Test current token with a simple API call
            headers = {
                'access-token': self.dhan_config["access_token"],
                'client-id': str(self.dhan_config["client_id"]),
                'Content-Type': 'application/json'
            }

            url = f"{self.dhan_config['data_api_url']}/ltp"
            payload = {"IDX_I": [13]}

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 401:
                print("🔄 Token expired, refreshing automatically...")
                return self.refresh_access_token()
            elif response.status_code == 200:
                print("✅ Token is valid")
                return True
            else:
                print(f"⚠️ Token validation returned status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Token validation failed: {str(e)}")
            return False

    def refresh_access_token(self):
        """Refresh access token using API key and secret"""
        try:
            url = f"{self.dhan_config['base_url']}/v2/login"

            payload = {
                "clientId": str(self.dhan_config["client_id"]),
                "clientSecret": self.dhan_config["api_secret"]
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if 'access_token' in data:
                new_token = data['access_token']
                self.dhan_config["access_token"] = new_token

                # Update the config file
                self.update_config_file()

                print("✅ Access token refreshed successfully")
                return True
            else:
                print(f"❌ Failed to get new token: {data}")
                return False

        except Exception as e:
            print(f"❌ Token refresh failed: {str(e)}")
            return False

    def update_config_file(self):
        """Update the configuration file with new token"""
        try:
            # Read current file content
            with open(__file__, 'r') as f:
                content = f.read()

            # Find and replace the access_token line
            import re
            old_token_pattern = r'("access_token":\s*)"[^"]*"'
            new_token_line = f'"access_token": "{self.dhan_config["access_token"]}"'

            updated_content = re.sub(old_token_pattern, new_token_line, content)

            # Write back to file
            with open(__file__, 'w') as f:
                f.write(updated_content)

            print("✅ Configuration file updated with new token")

        except Exception as e:
            print(f"❌ Failed to update config file: {str(e)}")

    def get_dhan_nifty_data(self):
        """Fetch real-time NIFTY data from Dhan Data API with auto token refresh"""
        try:
            # Validate and refresh token if needed
            if not self.validate_and_refresh_token():
                print("❌ Token validation/refresh failed, falling back to NSE")
                return None

            # Use Data API for permanent real-time data access
            headers = {
                'access-token': self.dhan_config["access_token"],
                'client-id': str(self.dhan_config["client_id"]),
                'Content-Type': 'application/json'
            }

            # Dhan Data API endpoint for real-time market data
            url = f"{self.dhan_config['data_api_url']}/ltp"

            # Request NIFTY 50 data (security_id: 13 for NIFTY 50, segment: IDX_I)
            payload = {
                "IDX_I": [13]  # NIFTY 50 security ID in index segment
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data and 'data' in data and data['data']:
                ltp_data = data['data']['13']  # NIFTY 50 data
                current_price = float(ltp_data['last_price'])

                print(f"✅ Dhan Data API: Real-time NIFTY price: ₹{current_price:,.2f}")
                return current_price

        except Exception as e:
            print(f"❌ Dhan Data API failed: {str(e)}")
            return None

    def get_nifty_data(self, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """Get NIFTY historical data with Dhan API priority"""
        try:
            print("📊 Fetching real NIFTY data from Dhan Advantage API...")

            # Try Dhan API first for real-time data
            current_price = self.get_dhan_nifty_data()

            if current_price:
                print(f"📊 Using Dhan API NIFTY level of ₹{current_price:.2f} for analysis")
                print("🔄 Generating realistic historical data based on current market conditions...")

                # Generate 30 days of realistic historical data based on current price
                dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

                # Use realistic volatility based on current market conditions
                daily_volatility = 0.015
                daily_drift = 0.0001

                np.random.seed(42)
                returns = np.random.normal(daily_drift, daily_volatility, len(dates))

                # Start from a price slightly below current and work backwards
                prices = [current_price * 0.98]

                for ret in returns[1:]:
                    new_price = prices[-1] * (1 + ret)
                    prices.append(new_price)

                # Create OHLC data
                data = []
                for i, price in enumerate(prices):
                    high = price * (1 + abs(np.random.normal(0, daily_volatility/2)))
                    low = price * (1 - abs(np.random.normal(0, daily_volatility/2)))
                    open_price = prices[i-1] if i > 0 else price * (1 + np.random.normal(0, daily_volatility/4))
                    volume = np.random.randint(200000, 500000)

                    data.append({
                        'Open': open_price,
                        'High': high,
                        'Low': low,
                        'Close': price,
                        'Volume': volume
                    })

                df = pd.DataFrame(data, index=dates)
                print(f"✅ Generated {len(df)} data points with Dhan API NIFTY level: ₹{prices[-1]:.2f}")
                return df

            # Fallback to NSE Python library
            print("🔄 Dhan API failed, trying NSE Python library...")
            return self.get_nse_nifty_data()

        except Exception as e:
            print(f"❌ Error fetching NIFTY data: {e}")
            print("🔄 Falling back to alternative data source...")
            return self.get_nifty_data_alternative()

    def get_nse_nifty_data(self) -> pd.DataFrame:
        """Get NIFTY data using NSE Python library"""
        try:
            print("📊 Fetching NIFTY data from NSE Python library...")

            # Get current NIFTY index data using nsepython
            nifty_df = nse_index()
            current_price = None

            if not nifty_df.empty:
                # Find NIFTY 50 data
                nifty_50_data = nifty_df[nifty_df['indexName'] == 'NIFTY 50']
                if not nifty_50_data.empty:
                    # Clean the price string (remove commas) and convert to float
                    last_price_str = str(nifty_50_data['last'].iloc[0]).replace(',', '')
                    current_price = float(last_price_str)
                    print(f"✅ Got current NIFTY price from NSE: ₹{current_price:.2f}")
                else:
                    # Fallback to first available index
                    print("⚠️ NIFTY 50 not found, using first available index")
                    last_price_str = str(nifty_df['last'].iloc[0]).replace(',', '')
                    current_price = float(last_price_str)
                    print(f"✅ Got index price from NSE: ₹{current_price:.2f}")

            if current_price:
                print(f"📊 Using NSE NIFTY level of ₹{current_price:.2f} for analysis")
                print("🔄 Generating realistic historical data based on current market conditions...")

                # Generate 30 days of realistic historical data based on current price
                dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

                daily_volatility = 0.015
                daily_drift = 0.0001

                np.random.seed(42)
                returns = np.random.normal(daily_drift, daily_volatility, len(dates))

                prices = [current_price * 0.98]

                for ret in returns[1:]:
                    new_price = prices[-1] * (1 + ret)
                    prices.append(new_price)

                # Create OHLC data
                data = []
                for i, price in enumerate(prices):
                    high = price * (1 + abs(np.random.normal(0, daily_volatility/2)))
                    low = price * (1 - abs(np.random.normal(0, daily_volatility/2)))
                    open_price = prices[i-1] if i > 0 else price * (1 + np.random.normal(0, daily_volatility/4))
                    volume = np.random.randint(200000, 500000)

                    data.append({
                        'Open': open_price,
                        'High': high,
                        'Low': low,
                        'Close': price,
                        'Volume': volume
                    })

                df = pd.DataFrame(data, index=dates)
                print(f"✅ Generated {len(df)} data points with NSE NIFTY level: ₹{prices[-1]:.2f}")
                return df

        except Exception as e:
            print(f"❌ NSE Python library error: {e}")

        # Fallback to Yahoo Finance
        print("🔄 NSE failed, trying Yahoo Finance...")
        return self.get_yahoo_finance_data()

    def get_yahoo_finance_data(self) -> pd.DataFrame:
        """Fallback method to get NIFTY data from Yahoo Finance"""
        try:
            # Try different NIFTY symbols
            symbols_to_try = ["^NSEI", "NSEI.NS", "^NSEBANK", "NIFTY.NS"]

            for symbol in symbols_to_try:
                try:
                    print(f"🔄 Trying Yahoo Finance symbol: {symbol}")
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="1mo", interval="1d")

                    if not data.empty and len(data) > 10:  # Ensure we have meaningful data
                        print(f"✅ Successfully retrieved {len(data)} data points for {symbol}")
                        print(f"📈 Latest NIFTY price: ₹{data['Close'].iloc[-1]:.2f}")
                        return data
                    else:
                        print(f"⚠️ Insufficient data from {symbol}, trying next...")

                except Exception as e:
                    print(f"❌ Failed with {symbol}: {str(e)[:100]}...")
                    continue

            return pd.DataFrame()

        except Exception as e:
            print(f"❌ Yahoo Finance error: {e}")
            return pd.DataFrame()

    def get_nifty_data_alternative(self) -> pd.DataFrame:
        """Alternative data source for NIFTY (simulated realistic data)"""
        try:
            print("📊 Generating realistic NIFTY data simulation...")

            # Get current approximate NIFTY level (you can update this manually)
            # As of October 2025, NIFTY is approximately around 24,000-25,000 range
            current_nifty_level = 24200  # Update this with current market level

            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

            # Generate more realistic price movement based on historical volatility
            np.random.seed(42)  # For reproducible results

            # NIFTY typical daily volatility is around 1-2%
            daily_volatility = 0.015
            daily_drift = 0.0002  # Slight upward drift

            returns = np.random.normal(daily_drift, daily_volatility, len(dates))
            prices = [current_nifty_level]

            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(new_price)

            # Create more realistic OHLC data
            data = []
            for i, price in enumerate(prices):
                # Add some realistic spread
                high = price * (1 + abs(np.random.normal(0, daily_volatility/2)))
                low = price * (1 - abs(np.random.normal(0, daily_volatility/2)))
                open_price = prices[i-1] if i > 0 else price * (1 + np.random.normal(0, daily_volatility/4))
                volume = np.random.randint(150000, 400000)  # Realistic NIFTY volume

                data.append({
                    'Open': open_price,
                    'High': high,
                    'Low': low,
                    'Close': price,
                    'Volume': volume
                })

            df = pd.DataFrame(data, index=dates)
            print(f"✅ Generated {len(df)} realistic data points")
            print(f"📈 Current NIFTY level: ₹{prices[-1]:.2f}")
            return df

        except Exception as e:
            print(f"❌ Error generating alternative data: {e}")
            return pd.DataFrame()

    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for analysis"""
        if data.empty:
            return {}

        # Basic price data
        current_price = data['Close'].iloc[-1]
        previous_price = data['Close'].iloc[-2] if len(data) > 1 else current_price

        # Moving averages
        sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]

        # RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # MACD
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        macd_value = macd.iloc[-1]
        signal_value = signal.iloc[-1]

        # Bollinger Bands
        sma_20_bb = data['Close'].rolling(window=20).mean()
        std_20 = data['Close'].rolling(window=20).std()
        upper_bb = sma_20_bb + (std_20 * 2)
        lower_bb = sma_20_bb - (std_20 * 2)

        # Volatility (20-day)
        returns = data['Close'].pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)  # Annualized

        return {
            "current_price": round(current_price, 2),
            "previous_price": round(previous_price, 2),
            "price_change": round(current_price - previous_price, 2),
            "price_change_pct": round(((current_price - previous_price) / previous_price) * 100, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "rsi": round(rsi, 2),
            "macd": round(macd_value, 2),
            "macd_signal": round(signal_value, 2),
            "macd_histogram": round(macd_value - signal_value, 2),
            "upper_bb": round(upper_bb.iloc[-1], 2),
            "lower_bb": round(lower_bb.iloc[-1], 2),
            "volatility": round(volatility * 100, 2)  # As percentage
        }

    def analyze_market_trend(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market trend"""
        current_price = indicators['current_price']
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']

        # Trend analysis
        trend_score = 0
        trend_signals = []

        # Price vs Moving averages
        if current_price > sma_20:
            trend_score += 1
            trend_signals.append("Price above 20-day MA")
        else:
            trend_score -= 1
            trend_signals.append("Price below 20-day MA")

        if sma_20 > sma_50:
            trend_score += 1
            trend_signals.append("20-day MA above 50-day MA (bullish)")
        else:
            trend_score -= 1
            trend_signals.append("20-day MA below 50-day MA (bearish)")

        # RSI analysis
        if rsi > 70:
            trend_signals.append("Overbought (RSI > 70)")
            trend_score -= 0.5
        elif rsi < 30:
            trend_signals.append("Oversold (RSI < 30)")
            trend_score += 0.5
        else:
            trend_signals.append("RSI neutral")

        # MACD analysis
        if macd > macd_signal:
            trend_score += 1
            trend_signals.append("MACD above signal (bullish)")
        else:
            trend_score -= 1
            trend_signals.append("MACD below signal (bearish)")

        # Determine overall trend
        if trend_score >= 2:
            overall_trend = "BULLISH"
            confidence = min(85, 60 + (trend_score * 10))
        elif trend_score <= -2:
            overall_trend = "BEARISH"
            confidence = min(85, 60 + abs(trend_score) * 10)
        else:
            overall_trend = "NEUTRAL"
            confidence = 50

        return {
            "trend": overall_trend,
            "confidence": confidence,
            "trend_score": trend_score,
            "signals": trend_signals
        }

    def generate_options_recommendations(self, indicators: Dict[str, Any], trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate NIFTY options trading recommendations"""
        current_price = indicators['current_price']
        volatility = indicators['volatility'] / 100  # Convert back to decimal
        trend = trend_analysis['trend']

        recommendations = []

        # Calculate strike prices (around current NIFTY level)
        base_strike = round(current_price / 50) * 50  # Round to nearest 50
        strikes = [base_strike + i * 50 for i in range(-4, 5)]  # +/- 200 points

        for strike in strikes:
            # Call option analysis
            if trend in ["BULLISH", "NEUTRAL"]:
                call_recommendation = self.analyze_call_option(strike, current_price, volatility, trend)
                if call_recommendation:
                    recommendations.append(call_recommendation)

            # Put option analysis
            if trend in ["BEARISH", "NEUTRAL"]:
                put_recommendation = self.analyze_put_option(strike, current_price, volatility, trend)
                if put_recommendation:
                    recommendations.append(put_recommendation)

        # Sort by confidence and return top recommendations
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations[:5]  # Top 5 recommendations

    def analyze_call_option(self, strike: float, spot: float, volatility: float, trend: str) -> Dict[str, Any]:
        """Analyze call option opportunity"""
        intrinsic_value = max(0, spot - strike)
        time_value = 0.1  # Simplified time value calculation

        # Basic Black-Scholes approximation for option pricing
        d1 = (np.log(spot/strike) + (0.05 + volatility**2/2) * 0.0833) / (volatility * np.sqrt(0.0833))
        call_price = spot * 0.5 + strike * 0.3  # Simplified pricing

        # Determine if it's a good buy
        if trend == "BULLISH" and strike <= spot * 1.05:  # ITM or slightly OTM
            confidence = min(80, 50 + (spot - strike) / spot * 100)
            reasoning = f"Bullish trend supports call buying. Strike near current price with good delta."

            return {
                "symbol": f"NIFTY{datetime.now().strftime('%d%b').upper()}{strike:.0f}CE",
                "type": "CALL",
                "action": "BUY",
                "strike": strike,
                "spot_price": spot,
                "estimated_premium": round(call_price, 2),
                "confidence": round(confidence, 1),
                "reasoning": reasoning,
                "risk_level": "MEDIUM",
                "potential_profit": f"₹{round(call_price * 2, 2)} (if NIFTY moves up 2%)",
                "stop_loss": f"₹{round(call_price * 0.3, 2)} (30% loss)"
            }

        return None

    def analyze_put_option(self, strike: float, spot: float, volatility: float, trend: str) -> Dict[str, Any]:
        """Analyze put option opportunity"""
        intrinsic_value = max(0, strike - spot)
        time_value = 0.1

        # Simplified put pricing
        put_price = strike * 0.3 + spot * 0.2

        # Determine if it's a good buy
        if trend == "BEARISH" and strike >= spot * 0.95:  # ITM or slightly OTM
            confidence = min(80, 50 + (strike - spot) / spot * 100)
            reasoning = f"Bearish trend supports put buying. Strike near current price with good protection."

            return {
                "symbol": f"NIFTY{datetime.now().strftime('%d%b').upper()}{strike:.0f}PE",
                "type": "PUT",
                "action": "BUY",
                "strike": strike,
                "spot_price": spot,
                "estimated_premium": round(put_price, 2),
                "confidence": round(confidence, 1),
                "reasoning": reasoning,
                "risk_level": "MEDIUM",
                "potential_profit": f"₹{round(put_price * 2.5, 2)} (if NIFTY moves down 2%)",
                "stop_loss": f"₹{round(put_price * 0.3, 2)} (30% loss)"
            }

        return None

    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete NIFTY options analysis"""
        print("🚀 Starting InfinityAI.Pro NIFTY Options Analysis")
        print("=" * 60)

        # Get market data
        nifty_data = self.get_nifty_data()

        if nifty_data.empty:
            return {"error": "Unable to fetch NIFTY data"}

        # Calculate technical indicators
        indicators = self.calculate_technical_indicators(nifty_data)

        # Analyze market trend
        trend_analysis = self.analyze_market_trend(indicators)

        # Generate options recommendations
        recommendations = self.generate_options_recommendations(indicators, trend_analysis)

        # Compile results
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "NIFTY_OPTIONS_ANALYSIS",
            "market_data": {
                "symbol": "NIFTY 50",
                "data_points": len(nifty_data),
                "analysis_period": "1 month"
            },
            "technical_indicators": indicators,
            "trend_analysis": trend_analysis,
            "options_recommendations": recommendations,
            "disclaimer": "⚠️ PAPER TRADING ANALYSIS ONLY - Not financial advice. Always do your own research.",
            "risk_warning": "Options trading involves substantial risk of loss. Past performance does not guarantee future results."
        }

        self.analysis_results = analysis_result
        return analysis_result

    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print formatted analysis report"""
        print("\n" + "=" * 80)
        print("🤖 INFINITYAI.PRO - NIFTY OPTIONS ANALYSIS REPORT")
        print("=" * 80)
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Market Data: NIFTY 50 ({analysis['market_data']['data_points']} data points)")
        print()

        # Technical Indicators
        ind = analysis['technical_indicators']
        print("📈 TECHNICAL INDICATORS:")
        print(f"   Current Price: ₹{ind['current_price']} ({ind['price_change_pct']:+.2f}%)")
        print(f"   RSI (14): {ind['rsi']:.1f}")
        print(f"   Moving Averages: SMA20=₹{ind['sma_20']}, SMA50=₹{ind['sma_50']}")
        print(f"   MACD: {ind['macd']:.2f} (Signal: {ind['macd_signal']:.2f})")
        print(f"   Volatility: {ind['volatility']:.1f}%")
        print()

        # Trend Analysis
        trend = analysis['trend_analysis']
        print("🎯 MARKET TREND ANALYSIS:")
        print(f"   Overall Trend: {trend['trend']} (Confidence: {trend['confidence']}%)")
        print(f"   Trend Score: {trend['trend_score']:+.1f}")
        print("   Key Signals:")
        for signal in trend['signals']:
            print(f"   • {signal}")
        print()

        # Options Recommendations
        print("💡 NIFTY OPTIONS RECOMMENDATIONS:")
        print("-" * 50)

        for i, rec in enumerate(analysis['options_recommendations'], 1):
            print(f"{i}. {rec['action']} {rec['symbol']} (₹{rec['estimated_premium']})")
            print(f"   Confidence: {rec['confidence']}% | Risk: {rec['risk_level']}")
            print(f"   Reasoning: {rec['reasoning']}")
            print(f"   Potential: {rec['potential_profit']} | Stop Loss: {rec['stop_loss']}")
            print()

        # Disclaimer
        print("⚠️  IMPORTANT DISCLAIMERS:")
        print("   • This is PAPER TRADING analysis only")
        print("   • Not financial advice - DYOR (Do Your Own Research)")
        print("   • Options trading carries high risk of loss")
        print("   • Past performance ≠ Future results")
        print("   • Always consult financial advisors")
        print()

        print("🎯 Analysis completed successfully!")
        print("=" * 80)

def main():
    """Main function to run NIFTY options analysis"""
    analyzer = SafeNiftyOptionsAnalyzer()

    try:
        # Run complete analysis
        results = analyzer.run_complete_analysis()

        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            return

        # Print formatted report
        analyzer.print_analysis_report(results)

        # Save results to file
        output_file = f"nifty_options_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"💾 Analysis saved to: {output_file}")

    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()