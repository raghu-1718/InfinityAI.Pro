"""
GIFT Nifty Signal Generator - MVP
Fetches GIFT Nifty data and generates trading signals based on overnight gaps
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class GIFTNiftySignalGenerator:
    """
    Generates pre-market trading signals from GIFT Nifty movements
    """
    
    def __init__(self):
        self.gift_nifty_current = None
        self.nifty_prev_close = None
        self.gap_pct = None
        self.bias = None
        self.recommended_strategy = None
    
    def fetch_gift_nifty_manual(self, gift_value, nifty_close):
        """
        Manual input for MVP
        User provides GIFT Nifty current value and Nifty previous close
        """
        self.gift_nifty_current = gift_value
        self.nifty_prev_close = nifty_close
        
        print(f"[INPUT] GIFT Nifty Current: {gift_value}")
        print(f"[INPUT] Nifty Previous Close: {nifty_close}")
    
    def calculate_gap(self):
        """Calculate overnight gap percentage"""
        if not self.gift_nifty_current or not self.nifty_prev_close:
            raise ValueError("GIFT Nifty and Nifty close values required")
        
        self.gap_pct = ((self.gift_nifty_current - self.nifty_prev_close) / 
                        self.nifty_prev_close) * 100
        
        return self.gap_pct
    
    def determine_bias(self):
        """Determine market bias from gap"""
        if self.gap_pct is None:
            self.calculate_gap()
        
        if self.gap_pct > 0.5:
            self.bias = "BULLISH"
        elif self.gap_pct < -0.5:
            self.bias = "BEARISH"
        else:
            self.bias = "NEUTRAL"
        
        return self.bias
    
    def get_strategy_recommendation(self):
        """Recommend best strategy based on GIFT Nifty signal"""
        if self.bias is None:
            self.determine_bias()
        
        gap_size = abs(self.gap_pct)
        
        # Large gaps (>1%) require different handling
        if gap_size > 1.0:
            if self.gap_pct > 0:
                # Strong bullish gap - trend continuation
                self.recommended_strategy = "MA_Crossover"
                reasoning = "Large positive gap suggests strong momentum"
            else:
                # Strong bearish gap - buy the dip
                self.recommended_strategy = "RSI_MeanReversion"
                reasoning = "Large negative gap creates oversold opportunity"
        
        # Medium gaps (0.5% - 1%)
        elif gap_size > 0.5:
            if self.bias == "BULLISH":
                self.recommended_strategy = "MA_Crossover"
                reasoning = "Bullish bias favors trend following"
            else:
                self.recommended_strategy = "RSI_MeanReversion"
                reasoning = "Bearish bias favors mean reversion"
        
        # Small gaps (<0.5%)
        else:
            self.recommended_strategy = "Hybrid_Auto"
            reasoning = "Neutral gap - use hybrid selector"
        
        return self.recommended_strategy, reasoning
    
    def get_position_size_adjustment(self):
        """Adjust position size based on gap magnitude"""
        gap_size = abs(self.gap_pct)
        
        if gap_size > 2.0:
            # Very large gap - high volatility expected
            multiplier = 0.7  # Reduce position size by 30%
        elif gap_size > 1.0:
            multiplier = 0.85  # Reduce by 15%
        else:
            multiplier = 1.0  # Normal position size
        
        return multiplier
    
    def get_stop_loss_adjustment(self):
        """Adjust stop-loss levels based on gap"""
        gap_size = abs(self.gap_pct)
        
        if gap_size > 2.0:
            sl_pct = 7.0  # Wider stop on high volatility days
        elif gap_size > 1.0:
            sl_pct = 6.0
        else:
            sl_pct = 5.0  # Standard stop-loss
        
        return sl_pct
    
    def generate_complete_signal(self):
        """Generate complete trading signal with all parameters"""
        gap = self.calculate_gap()
        bias = self.determine_bias()
        strategy, reasoning = self.get_strategy_recommendation()
        position_multiplier = self.get_position_size_adjustment()
        stop_loss = self.get_stop_loss_adjustment()
        
        signal = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gift_nifty': self.gift_nifty_current,
            'nifty_prev_close': self.nifty_prev_close,
            'gap_points': self.gift_nifty_current - self.nifty_prev_close,
            'gap_percent': round(gap, 2),
            'bias': bias,
            'recommended_strategy': strategy,
            'reasoning': reasoning,
            'position_size_multiplier': position_multiplier,
            'stop_loss_pct': stop_loss,
            'volatility_expectation': 'HIGH' if abs(gap) > 1.0 else 'NORMAL'
        }
        
        return signal
    
    def print_signal_report(self, signal):
        """Print formatted signal report"""
        print("\n" + "=" * 80)
        print("  GIFT NIFTY PRE-MARKET SIGNAL")
        print("=" * 80)
        
        print(f"\nTime: {signal['timestamp']}")
        print(f"\nMarket Data:")
        print(f"  GIFT Nifty: {signal['gift_nifty']:.2f}")
        print(f"  Nifty Prev Close: {signal['nifty_prev_close']:.2f}")
        print(f"  Overnight Gap: {signal['gap_points']:.2f} points ({signal['gap_percent']:+.2f}%)")
        
        print(f"\nMarket Analysis:")
        print(f"  Bias: {signal['bias']}")
        print(f"  Expected Volatility: {signal['volatility_expectation']}")
        
        print(f"\nTrading Recommendation:")
        print(f"  Strategy: {signal['recommended_strategy']}")
        print(f"  Reasoning: {signal['reasoning']}")
        print(f"  Position Size: {signal['position_size_multiplier']*100:.0f}% of normal")
        print(f"  Stop Loss: {signal['stop_loss_pct']}%")
        
        # Additional guidance
        print(f"\nExecution Guidance:")
        if signal['bias'] == 'BULLISH':
            print(f"  [+] Look for long opportunities")
            print(f"  [+] Favor breakout trades")
            print(f"  [+] Trail stop-loss aggressively")
        elif signal['bias'] == 'BEARISH':
            print(f"  [-] Wait for oversold conditions")
            print(f"  [-] Quick profit taking")
            print(f"  [-] Tight stop-losses")
        else:
            print(f"  [=] Normal strategy execution")
            print(f"  [=] Wait for clear signals")
        
        print("\n" + "=" * 80)

def demo_gift_nifty_signals():
    """Demo with sample scenarios"""
    print("=" * 80)
    print("  GIFT NIFTY SIGNAL GENERATOR - DEMO")
    print("=" * 80)
    
    scenarios = [
        {"name": "Bullish Gap", "gift": 23850, "nifty": 23500, "description": "Strong overnight rally"},
        {"name": "Bearish Gap", "gift": 23200, "nifty": 23500, "description": "Sharp overnight drop"},
        {"name": "Neutral", "gift": 23510, "nifty": 23500, "description": "Flat overnight"},
    ]
    
    for scenario in scenarios:
        print(f"\n\n{'='*80}")
        print(f"  SCENARIO: {scenario['name']} - {scenario['description']}")
        print(f"{'='*80}")
        
        gen = GIFTNiftySignalGenerator()
        gen.fetch_gift_nifty_manual(scenario['gift'], scenario['nifty'])
        signal = gen.generate_complete_signal()
        gen.print_signal_report(signal)

if __name__ == "__main__":
    demo_gift_nifty_signals()
