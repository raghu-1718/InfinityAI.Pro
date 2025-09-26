#!/usr/bin/env python3
"""
InfinityAI.Pro - API Key Configuration
Securely configure your API keys for enhanced trading intelligence.
"""

import os
import json
import getpass
from pathlib import Path

def configure_api_keys():
    """Securely configure API keys"""
    print("🔐 InfinityAI.Pro API Key Configuration")
    print("=" * 50)
    print("Configure your API keys for enhanced trading intelligence:")
    print("• Perplexity: Market news & sentiment analysis")
    print("• OpenAI: Strategy narration & risk assessment")
    print("• TradingView: Market data (optional)")
    print()

    # Check if config exists
    config_path = Path("utils/config.py")
    if not config_path.exists():
        print("❌ Config file not found. Please run from backend directory.")
        return False

    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()

    # Get API keys securely
    print("📡 API Key Configuration:")
    print("-" * 30)

    # Perplexity API Key
    perplexity_key = getpass.getpass("🔑 Perplexity API Key (press Enter to skip): ").strip()
    if perplexity_key:
        content = content.replace('"api_key": None', f'"api_key": "{perplexity_key}"', 1)
        print("✅ Perplexity API key configured")
    else:
        print("⚠️  Perplexity API key skipped")

    # OpenAI API Key
    openai_key = getpass.getpass("🤖 OpenAI API Key (press Enter to skip): ").strip()
    if openai_key:
        content = content.replace('"api_key": None', f'"api_key": "{openai_key}"', 1)
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key skipped")

    # TradingView API Key (optional)
    tradingview_key = getpass.getpass("📊 TradingView API Key (press Enter to skip): ").strip()
    if tradingview_key:
        content = content.replace('"api_key": None', f'"api_key": "{tradingview_key}"', 1)
        print("✅ TradingView API key configured")
    else:
        print("⚠️  TradingView API key skipped")

    # Write back config
    with open(config_path, 'w') as f:
        f.write(content)

    print("\n🎯 Configuration Summary:")
    print("-" * 30)
    if perplexity_key:
        print("✅ Perplexity: Enabled (Market Intelligence)")
    else:
        print("❌ Perplexity: Disabled")

    if openai_key:
        print("✅ OpenAI: Enabled (Strategy Narration)")
    else:
        print("❌ OpenAI: Disabled")

    if tradingview_key:
        print("✅ TradingView: Enabled (Market Data)")
    else:
        print("❌ TradingView: Disabled")

    print("\n🚀 Ready to start enhanced trading!")
    return True

def test_api_connections():
    """Test API connections"""
    print("\n🧪 Testing API Connections...")
    print("-" * 30)

    try:
        from utils.config import CONFIG

        # Test Perplexity
        if CONFIG.PERPLEXITY.get('api_key'):
            try:
                from services.perplexity_client import PerplexityClient
                client = PerplexityClient(CONFIG.PERPLEXITY['api_key'])
                print("✅ Perplexity: Connection OK")
            except Exception as e:
                print(f"❌ Perplexity: {str(e)}")
        else:
            print("⚠️  Perplexity: No API key configured")

        # Test OpenAI
        if CONFIG.OPENAI.get('api_key'):
            try:
                from services.openai_client import OpenAIClient
                client = OpenAIClient(CONFIG.OPENAI['api_key'], CONFIG.OPENAI.get('model', 'gpt-4'))
                print("✅ OpenAI: Connection OK")
            except Exception as e:
                print(f"❌ OpenAI: {str(e)}")
        else:
            print("⚠️  OpenAI: No API key configured")

        # Test TradingView
        if CONFIG.TRADINGVIEW.get('api_key'):
            print("✅ TradingView: API key configured")
        else:
            print("⚠️  TradingView: No API key configured")

    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")

def main():
    """Main configuration function"""
    # Change to backend directory if not already there
    if not Path("utils/config.py").exists():
        if Path("../backend/utils/config.py").exists():
            os.chdir("../backend")
        else:
            print("❌ Please run this script from the backend directory")
            return

    # Configure keys
    if configure_api_keys():
        # Test connections
        test_api_connections()

        print("\n🎯 Next Steps:")
        print("1. Start the enhanced trading system:")
        print("   python services/live_trader.py")
        print("2. Monitor AI insights in the console")
        print("3. Check trade_logs/trades.csv for results")

if __name__ == "__main__":
    main()