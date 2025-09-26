#!/usr/bin/env python3
"""
InfinityAI.Pro - Enhanced Trading System Setup
==============================================

This script helps you configure the AI-enhanced trading system with Perplexity and OpenAI integration.

Requirements:
1. Perplexity API key (for market news and sentiment analysis)
2. OpenAI API key (for strategy narration and risk analysis)

Usage:
1. Run this script: python setup_trading.py
2. Enter your API keys when prompted
3. The system will start with AI-enhanced trading

The enhanced system includes:
- Real-time market news analysis via Perplexity
- AI-powered strategy narration via OpenAI
- Sentiment-enhanced trading signals
- Risk assessment and portfolio insights
- Hybrid quant + AI decision making
"""

import os
import json
import sys
from pathlib import Path

def setup_api_keys():
    """Configure API keys for Perplexity and OpenAI"""
    print("🔑 InfinityAI.Pro API Configuration")
    print("=" * 40)

    # Check if config exists
    config_path = Path("utils/config.py")
    if not config_path.exists():
        print("❌ Config file not found. Please run from backend directory.")
        return False

    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()

    # Get API keys from user
    print("\n📡 Perplexity API (Market News & Sentiment)")
    perplexity_key = input("Enter your Perplexity API key (or press Enter to skip): ").strip()

    print("\n🤖 OpenAI API (Strategy Narration & Risk Analysis)")
    openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()

    # Update config content
    if perplexity_key:
        content = content.replace('"api_key": None', f'"api_key": "{perplexity_key}"', 1)
        print("✅ Perplexity API key configured")

    if openai_key:
        content = content.replace('"api_key": None', f'"api_key": "{openai_key}"', 1)
        print("✅ OpenAI API key configured")

    # Write back config
    with open(config_path, 'w') as f:
        f.write(content)

    print("\n🎯 Configuration complete!")
    return True

def start_trading():
    """Start the enhanced trading system"""
    print("\n🚀 Starting InfinityAI.Pro Enhanced Trading System")
    print("=" * 50)

    print("📊 System Configuration:")
    print(f"   • Capital: ₹{11000}")
    print(f"   • Risk per trade: 3%")
    print(f"   • Daily profit target: 25%")
    print(f"   • Scan frequency: 15 seconds")
    print(f"   • Minimum trade score: 0.55")
    print(f"   • Focus: MCX commodities (extended hours)")

    print("\n🧠 AI Enhancements:")
    print("   • Perplexity: Real-time market news & sentiment")
    print("   • OpenAI: Strategy narration & risk analysis")
    print("   • Hybrid signals: Quant + AI intelligence")

    print("\n⚡ Starting live trading with AI intelligence...")

    # Run the trader
    os.system("python services/live_trader.py")

def main():
    """Main setup function"""
    print(__doc__)

    # Change to backend directory if not already there
    if not Path("utils/config.py").exists():
        if Path("../backend/utils/config.py").exists():
            os.chdir("../backend")
        else:
            print("❌ Please run this script from the backend directory")
            sys.exit(1)

    # Setup API keys
    if not setup_api_keys():
        return

    # Confirm before starting
    print("\n⚠️  WARNING: This will start LIVE TRADING")
    confirm = input("Are you sure you want to start live trading? (yes/no): ").lower().strip()

    if confirm in ['yes', 'y']:
        start_trading()
    else:
        print("❌ Trading cancelled. You can run this script again when ready.")

if __name__ == "__main__":
    main()