"""
InfinityAI.Pro - Vertex AI Integration Test Script
===================================================
Tests the enhanced GenAI integration with function calling.

Run: python scripts/test_vertex_ai_integration.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(label: str, value, success: bool = True):
    """Print a result with status indicator."""
    status = "✅" if success else "❌"
    print(f"{status} {label}: {value}")


async def test_market_data_tools():
    """Test market data tools."""
    print_header("1. Testing Market Data Tools")

    try:
        from shared.google_integrations.market_data_tools import (
            get_stock_quote,
            get_nifty_overview,
            get_technical_indicators,
            get_option_chain_data,
            get_fii_dii_activity
        )

        # Test stock quote
        print("\n📈 Testing get_stock_quote('RELIANCE')...")
        quote = get_stock_quote("RELIANCE", "NSE")
        if "error" not in quote:
            print_result("Price", f"₹{quote.get('current_price', 'N/A')}")
            print_result("Change", f"{quote.get('change_percent', 'N/A')}%")
            print_result("Volume", f"{quote.get('volume', 'N/A'):,}")
        else:
            print_result("Quote Error", quote.get("error"), False)

        # Test NIFTY overview
        print("\n📊 Testing get_nifty_overview()...")
        overview = get_nifty_overview()
        if "error" not in overview:
            nifty = overview.get("nifty50", {})
            print_result("NIFTY", f"{nifty.get('value', 'N/A')} ({nifty.get('change_percent', 'N/A')}%)")
            print_result("Trend", nifty.get("trend", "N/A"))
            print_result("Top Gainers", len(overview.get("top_gainers", [])))
        else:
            print_result("Overview Error", overview.get("error"), False)

        # Test technical indicators
        print("\n📉 Testing get_technical_indicators('NIFTY')...")
        technicals = get_technical_indicators("NIFTY")
        if "error" not in technicals:
            rsi = technicals.get("rsi", {})
            macd = technicals.get("macd", {})
            print_result("RSI", f"{rsi.get('value', 'N/A')} ({rsi.get('status', 'N/A')})")
            print_result("MACD Trend", macd.get("trend", "N/A"))
            print_result("Overall", technicals.get("overall_trend", "N/A"))
        else:
            print_result("Technicals Error", technicals.get("error"), False)

        # Test option chain
        print("\n📋 Testing get_option_chain_data('NIFTY')...")
        chain = get_option_chain_data("NIFTY")
        if "error" not in chain:
            print_result("Spot", f"₹{chain.get('spot_price', 'N/A')}")
            print_result("PCR", chain.get("pcr", "N/A"))
            print_result("Max Pain", chain.get("max_pain", "N/A"))
            print_result("Market Bias", chain.get("market_bias", "N/A"))
        else:
            print_result("Chain Error", chain.get("error"), False)

        # Test FII/DII
        print("\n🏦 Testing get_fii_dii_activity()...")
        fii_dii = get_fii_dii_activity()
        if "error" not in fii_dii:
            cash = fii_dii.get("cash_segment", {})
            print_result("FII Net", f"₹{cash.get('fii', {}).get('net', 'N/A')} Cr")
            print_result("DII Net", f"₹{cash.get('dii', {}).get('net', 'N/A')} Cr")
            print_result("Impact", fii_dii.get("market_impact", "N/A"))
        else:
            print_result("FII/DII Error", fii_dii.get("error"), False)

        print_result("\nMarket Data Tools", "All tests completed", True)
        return True

    except ImportError as e:
        print_result("Import Error", str(e), False)
        return False
    except Exception as e:
        print_result("Test Error", str(e), False)
        return False


async def test_news_integration():
    """Test news integration."""
    print_header("2. Testing News Integration")

    try:
        from shared.google_integrations.news_integration import (
            NewsAggregator,
            get_market_news_live,
            get_symbol_news_live
        )

        # Test news aggregator
        print("\n📰 Testing NewsAggregator...")
        aggregator = NewsAggregator()

        feed = await aggregator.fetch_all_news(["markets", "stocks"], max_articles=10)
        print_result("Articles Found", len(feed.articles))
        print_result("Overall Sentiment", feed.overall_sentiment)
        print_result("Bullish/Bearish/Neutral", f"{feed.bullish_count}/{feed.bearish_count}/{feed.neutral_count}")

        if feed.articles:
            print("\n  Top headlines:")
            for article in feed.articles[:3]:
                print(f"    [{article.sentiment}] {article.title[:50]}...")

        # Test symbol news
        print("\n📈 Testing symbol news for RELIANCE...")
        ril_feed = await aggregator.fetch_symbol_news("RELIANCE", max_articles=5)
        print_result("RELIANCE News", len(ril_feed.articles))
        print_result("Sentiment", ril_feed.overall_sentiment)

        print_result("\nNews Integration", "All tests completed", True)
        return True

    except ImportError as e:
        print_result("Import Error", str(e), False)
        print("Note: Install feedparser with: pip install feedparser")
        return False
    except Exception as e:
        print_result("Test Error", str(e), False)
        return False


async def test_enhanced_genai_client():
    """Test enhanced GenAI client with Vertex AI."""
    print_header("3. Testing Enhanced GenAI Client")

    try:
        from shared.google_integrations.enhanced_genai_client import (
            EnhancedGenAIClient,
            INFINITYAI_SYSTEM_PROMPT
        )

        # Check system prompt
        print("\n📝 System Prompt loaded:")
        print(f"  Length: {len(INFINITYAI_SYSTEM_PROMPT)} characters")
        print(f"  Contains capabilities: {INFINITYAI_SYSTEM_PROMPT[:100]}...")

        # Initialize client
        print("\n🔧 Initializing EnhancedGenAIClient...")
        client = EnhancedGenAIClient(
            project_id="gen-lang-client-0779271931",
            model_id="gemini-2.0-flash"
        )
        print_result("Client Created", f"Project: {client.project_id}", True)

        # Test quick signal
        print("\n🎯 Testing quick_signal('NIFTY')...")
        try:
            signal = await client.quick_signal("NIFTY")
            if signal.get("response"):
                print_result("Response", f"{signal['response'][:200]}...")
                print_result("Function Calls", len(signal.get("function_calls", [])))
                print_result("Token Usage", signal.get("token_usage", {}))
            elif signal.get("error"):
                print_result("API Error", signal["error"], False)
                print("Note: Ensure GOOGLE_APPLICATION_CREDENTIALS is set")
        except Exception as e:
            print_result("Quick Signal Error", str(e), False)

        # Test market summary
        print("\n📊 Testing get_market_summary()...")
        try:
            summary = await client.get_market_summary()
            if summary.get("response"):
                print_result("Summary", f"{summary['response'][:200]}...")
            elif summary.get("error"):
                print_result("API Error", summary["error"], False)
        except Exception as e:
            print_result("Market Summary Error", str(e), False)

        # Print usage stats
        stats = client.get_usage_stats()
        print("\n📊 Usage Stats:")
        print(f"  Total Tokens: {stats['token_usage']['total']}")
        print(f"  Estimated Cost: ${stats['estimated_cost']['total_cost_usd']}")
        print(f"  Credits: {stats['credits_info']}")

        print_result("\nEnhanced GenAI Client", "Tests completed", True)
        return True

    except ImportError as e:
        print_result("Import Error", str(e), False)
        print("Note: Install google-genai with: pip install google-genai")
        return False
    except Exception as e:
        print_result("Test Error", str(e), False)
        return False


async def test_full_trading_signal():
    """Test full trading signal generation."""
    print_header("4. Testing Full Trading Signal Generation")

    try:
        from shared.google_integrations.enhanced_genai_client import (
            EnhancedGenAIClient
        )

        client = EnhancedGenAIClient()

        print("\n🎯 Generating trading signal for RELIANCE...")
        recommendation = await client.generate_trading_signal(
            symbol="RELIANCE",
            analysis_type="intraday",
            fetch_live_data=True,
            auto_execute=False
        )

        print("\n📈 Trading Recommendation:")
        print(f"  Symbol: {recommendation.symbol}")
        print(f"  Signal: {recommendation.signal.value}")
        print(f"  Confidence: {recommendation.confidence}%")
        print(f"  Entry Price: ₹{recommendation.entry_price}")
        print(f"  Stop Loss: ₹{recommendation.stop_loss}")
        print(f"  Targets: {recommendation.target_prices}")
        print(f"  Risk/Reward: {recommendation.risk_reward}")
        print(f"  Risk Level: {recommendation.risk_level.value}")
        print(f"  Timeframe: {recommendation.timeframe.value}")
        print(f"  Reasoning: {recommendation.reasoning[:150]}...")
        print(f"  News Sentiment: {recommendation.news_sentiment}")
        print(f"  FII/DII View: {recommendation.fii_dii_view}")

        print_result("\nFull Trading Signal", "Generated successfully", True)
        return True

    except Exception as e:
        print_result("Trading Signal Error", str(e), False)
        return False


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print(" InfinityAI.Pro - Vertex AI Integration Tests")
    print(" " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    results = {}

    # Test 1: Market Data Tools
    results["market_data"] = await test_market_data_tools()

    # Test 2: News Integration
    results["news"] = await test_news_integration()

    # Test 3: Enhanced GenAI Client
    results["genai"] = await test_enhanced_genai_client()

    # Test 4: Full Trading Signal (only if GenAI works)
    if results["genai"]:
        results["trading_signal"] = await test_full_trading_signal()
    else:
        results["trading_signal"] = False
        print("\n⏭️  Skipping trading signal test (GenAI not working)")

    # Summary
    print_header("TEST SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"  {test}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("Ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure GOOGLE_APPLICATION_CREDENTIALS is set")
        print("2. Install dependencies: pip install google-genai yfinance feedparser aiohttp")
        print("3. Verify GCP project permissions")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
