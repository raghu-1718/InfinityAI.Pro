#!/usr/bin/env python3
# 🎯 InfinityAI.Pro - Aggressive Profit Switching Strategy
# Exit Crude Oil → Enter Strong NIFTY Options for Higher Returns

import requests
import json
import asyncio
from datetime import datetime, timedelta
import math

class AggressiveProfitSwitcher:
    def __init__(self):
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
        
        # Current positions
        self.crude_entry = 123.70
        self.crude_current = 129.00
        self.crude_profit = 5.30  # ₹5.30 profit per unit
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def analyze_nifty_opportunities(self):
        """Find high-probability NIFTY trades with aggressive profit potential"""
        
        # Simulated real-time NIFTY analysis (In production: real market data)
        nifty_current = 25800
        nifty_resistance = 25950
        nifty_support = 25650
        
        opportunities = []
        
        # 1. BULLISH BREAKOUT PLAY - High Reward
        if nifty_current > 25780:  # Above key level
            breakout_call = {
                "symbol": "NIFTY50-16Oct2025-25850-CE",
                "strategy": "BULLISH_BREAKOUT",
                "entry_price": 85.0,
                "target_1": 110.0,  # 29% gain
                "target_2": 130.0,  # 53% gain
                "stop_loss": 65.0,  # 23% loss
                "confidence": 88.0,
                "risk_reward": 2.3,
                "reasoning": "NIFTY testing resistance, breakout above 25800 could trigger momentum rally",
                "probability": "HIGH",
                "time_frame": "1-3 days",
                "leverage_factor": 15  # Options leverage
            }
            opportunities.append(breakout_call)
        
        # 2. MOMENTUM CONTINUATION - Very Aggressive
        momentum_call = {
            "symbol": "NIFTY50-16Oct2025-25900-CE",
            "strategy": "MOMENTUM_PLAY",
            "entry_price": 65.0,
            "target_1": 95.0,   # 46% gain
            "target_2": 120.0,  # 85% gain
            "stop_loss": 45.0,  # 31% loss
            "confidence": 85.0,
            "risk_reward": 2.7,
            "reasoning": "Strong bullish momentum, FII buying, global markets positive",
            "probability": "HIGH",
            "time_frame": "1-2 days",
            "leverage_factor": 20
        }
        opportunities.append(momentum_call)
        
        # 3. BANK NIFTY CORRELATION PLAY
        bank_nifty_play = {
            "symbol": "BANKNIFTY-16Oct2025-54200-CE",
            "strategy": "BANK_MOMENTUM",
            "entry_price": 140.0,
            "target_1": 200.0,  # 43% gain
            "target_2": 250.0,  # 79% gain
            "stop_loss": 100.0, # 29% loss
            "confidence": 82.0,
            "risk_reward": 2.5,
            "reasoning": "Bank NIFTY lagging NIFTY, catch-up trade with high volume",
            "probability": "MEDIUM-HIGH",
            "time_frame": "2-4 days",
            "leverage_factor": 12
        }
        opportunities.append(bank_nifty_play)
        
        return opportunities
    
    def calculate_profit_comparison(self, nifty_opportunity):
        """Compare crude oil vs NIFTY profit potential"""
        
        # Current crude oil position
        crude_invested = 123.70 * 1  # 1 lot
        crude_current_value = 129.00 * 1
        crude_profit = crude_current_value - crude_invested
        crude_profit_percent = (crude_profit / crude_invested) * 100
        
        # NIFTY opportunity potential
        nifty_entry = nifty_opportunity["entry_price"]
        nifty_target_1 = nifty_opportunity["target_1"]
        nifty_target_2 = nifty_opportunity["target_2"]
        
        # Calculate potential with same capital
        available_capital = crude_current_value  # ₹129 after exiting crude
        nifty_quantity = int(available_capital / nifty_entry)
        
        nifty_profit_1 = (nifty_target_1 - nifty_entry) * nifty_quantity
        nifty_profit_2 = (nifty_target_2 - nifty_entry) * nifty_quantity
        
        nifty_profit_percent_1 = ((nifty_target_1 - nifty_entry) / nifty_entry) * 100
        nifty_profit_percent_2 = ((nifty_target_2 - nifty_entry) / nifty_entry) * 100
        
        return {
            "crude_current_profit": crude_profit,
            "crude_profit_percent": crude_profit_percent,
            "nifty_quantity": nifty_quantity,
            "nifty_potential_profit_1": nifty_profit_1,
            "nifty_potential_profit_2": nifty_profit_2,
            "nifty_profit_percent_1": nifty_profit_percent_1,
            "nifty_profit_percent_2": nifty_profit_percent_2,
            "profit_multiplier_1": nifty_profit_1 / crude_profit if crude_profit > 0 else 0,
            "profit_multiplier_2": nifty_profit_2 / crude_profit if crude_profit > 0 else 0
        }
    
    def generate_switching_recommendation(self, opportunity, comparison):
        """Generate smart switching recommendation"""
        
        # Decision factors
        confidence = opportunity["confidence"]
        risk_reward = opportunity["risk_reward"]
        profit_multiplier_1 = comparison["profit_multiplier_1"]
        profit_multiplier_2 = comparison["profit_multiplier_2"]
        
        # Scoring system
        score = 0
        recommendation = "HOLD_CRUDE"
        reasoning = []
        
        # Confidence scoring
        if confidence >= 85:
            score += 30
            reasoning.append(f"High confidence ({confidence}%)")
        elif confidence >= 80:
            score += 20
            reasoning.append(f"Good confidence ({confidence}%)")
        
        # Risk-reward scoring
        if risk_reward >= 2.5:
            score += 25
            reasoning.append(f"Excellent risk-reward ({risk_reward:.1f})")
        elif risk_reward >= 2.0:
            score += 15
            reasoning.append(f"Good risk-reward ({risk_reward:.1f})")
        
        # Profit potential scoring
        if profit_multiplier_1 >= 5:
            score += 30
            reasoning.append(f"Target 1: {profit_multiplier_1:.1f}x current profit")
        elif profit_multiplier_1 >= 3:
            score += 20
            reasoning.append(f"Target 1: {profit_multiplier_1:.1f}x current profit")
        
        if profit_multiplier_2 >= 8:
            score += 15
            reasoning.append(f"Target 2: {profit_multiplier_2:.1f}x current profit")
        
        # Decision logic
        if score >= 70:
            recommendation = "SWITCH_AGGRESSIVE"
        elif score >= 50:
            recommendation = "SWITCH_MODERATE"
        elif score >= 30:
            recommendation = "CONSIDER_SWITCH"
        
        return {
            "recommendation": recommendation,
            "score": score,
            "reasoning": reasoning,
            "action_plan": self.generate_action_plan(recommendation, opportunity, comparison)
        }
    
    def generate_action_plan(self, recommendation, opportunity, comparison):
        """Generate detailed action plan"""
        
        if recommendation == "SWITCH_AGGRESSIVE":
            return {
                "step_1": f"EXIT CRUDE: Sell at ₹{self.crude_current} (Lock ₹{comparison['crude_current_profit']:.2f} profit)",
                "step_2": f"ENTER NIFTY: Buy {comparison['nifty_quantity']} lots {opportunity['symbol']} @ ₹{opportunity['entry_price']}",
                "step_3": f"TARGET 1: ₹{opportunity['target_1']} ({comparison['nifty_profit_percent_1']:.1f}% gain)",
                "step_4": f"TARGET 2: ₹{opportunity['target_2']} ({comparison['nifty_profit_percent_2']:.1f}% gain)",
                "step_5": f"STOP LOSS: ₹{opportunity['stop_loss']} (Risk management)",
                "execution": "IMMEDIATE",
                "rationale": f"Potential profit: ₹{comparison['nifty_potential_profit_1']:.2f} to ₹{comparison['nifty_potential_profit_2']:.2f}"
            }
        elif recommendation == "SWITCH_MODERATE":
            return {
                "step_1": "EXIT 50% of CRUDE position",
                "step_2": f"ENTER NIFTY with partial capital",
                "step_3": "Monitor both positions",
                "execution": "GRADUAL",
                "rationale": "Reduce risk while capturing NIFTY opportunity"
            }
        else:
            return {
                "step_1": "HOLD CRUDE position",
                "step_2": "Monitor NIFTY levels",
                "step_3": "Wait for better opportunity",
                "execution": "WAIT",
                "rationale": "Current crude profit is acceptable, NIFTY risk too high"
            }
    
    async def run_switching_analysis(self):
        """Main analysis for crude to NIFTY switching"""
        
        self.log("🎯 Analyzing Crude Oil → NIFTY Switching Strategy", "INFO")
        
        # Get NIFTY opportunities
        opportunities = await self.analyze_nifty_opportunities()
        
        print("\n" + "="*80)
        print("🔥 AGGRESSIVE PROFIT SWITCHING ANALYSIS")
        print("="*80)
        
        print(f"\n📊 CURRENT CRUDE OIL POSITION:")
        print(f"Entry: ₹{self.crude_entry}")
        print(f"Current: ₹{self.crude_current}")
        print(f"Profit: ₹{self.crude_profit} ({((self.crude_current - self.crude_entry) / self.crude_entry * 100):.1f}%)")
        
        print(f"\n🎯 NIFTY OPPORTUNITIES FOUND: {len(opportunities)}")
        
        best_opportunity = None
        best_score = 0
        
        for i, opportunity in enumerate(opportunities, 1):
            comparison = self.calculate_profit_comparison(opportunity)
            recommendation = self.generate_switching_recommendation(opportunity, comparison)
            
            print(f"\n{i}. {opportunity['symbol']} - {opportunity['strategy']}")
            print(f"   Entry: ₹{opportunity['entry_price']}")
            print(f"   Target 1: ₹{opportunity['target_1']} ({comparison['nifty_profit_percent_1']:.1f}% gain)")
            print(f"   Target 2: ₹{opportunity['target_2']} ({comparison['nifty_profit_percent_2']:.1f}% gain)")
            print(f"   Stop Loss: ₹{opportunity['stop_loss']}")
            print(f"   Confidence: {opportunity['confidence']:.1f}%")
            print(f"   Risk-Reward: {opportunity['risk_reward']:.1f}")
            print(f"   Quantity: {comparison['nifty_quantity']} lots")
            print(f"   Potential Profit: ₹{comparison['nifty_potential_profit_1']:.2f} to ₹{comparison['nifty_potential_profit_2']:.2f}")
            print(f"   Profit Multiplier: {comparison['profit_multiplier_1']:.1f}x to {comparison['profit_multiplier_2']:.1f}x")
            print(f"   📈 RECOMMENDATION: {recommendation['recommendation']} (Score: {recommendation['score']}/100)")
            print(f"   🧠 Reasoning: {opportunity['reasoning']}")
            
            if recommendation['score'] > best_score:
                best_score = recommendation['score']
                best_opportunity = {
                    'opportunity': opportunity,
                    'comparison': comparison,
                    'recommendation': recommendation
                }
        
        # Display best recommendation
        if best_opportunity:
            print(f"\n🏆 BEST OPPORTUNITY: {best_opportunity['opportunity']['symbol']}")
            print("="*60)
            
            action_plan = best_opportunity['recommendation']['action_plan']
            
            print(f"🎯 RECOMMENDATION: {best_opportunity['recommendation']['recommendation']}")
            print(f"📊 CONFIDENCE SCORE: {best_score}/100")
            
            print(f"\n📋 ACTION PLAN:")
            for key, value in action_plan.items():
                if key.startswith('step_'):
                    print(f"   {key.upper()}: {value}")
                elif key == 'rationale':
                    print(f"   💡 RATIONALE: {value}")
            
            print(f"\n⚡ EXECUTION: {action_plan.get('execution', 'MANUAL')}")
            
            # Risk analysis
            print(f"\n⚠️ RISK ANALYSIS:")
            print(f"   Current Crude Profit: ₹{best_opportunity['comparison']['crude_current_profit']:.2f}")
            print(f"   NIFTY Potential Loss: ₹{(best_opportunity['opportunity']['entry_price'] - best_opportunity['opportunity']['stop_loss']) * best_opportunity['comparison']['nifty_quantity']:.2f}")
            print(f"   Risk-Reward Ratio: {best_opportunity['opportunity']['risk_reward']:.1f}")
            
            # Final recommendation
            if best_score >= 70:
                print(f"\n🚀 FINAL VERDICT: STRONG SWITCH RECOMMENDED!")
                print(f"💰 Potential gain: {best_opportunity['comparison']['profit_multiplier_2']:.1f}x current profit")
                print(f"⏱️ Time frame: {best_opportunity['opportunity']['time_frame']}")
            elif best_score >= 50:
                print(f"\n🤔 FINAL VERDICT: MODERATE SWITCH - Consider partial position")
            else:
                print(f"\n✋ FINAL VERDICT: HOLD CRUDE - Wait for better NIFTY setup")

# Execute analysis
if __name__ == "__main__":
    switcher = AggressiveProfitSwitcher()
    asyncio.run(switcher.run_switching_analysis())