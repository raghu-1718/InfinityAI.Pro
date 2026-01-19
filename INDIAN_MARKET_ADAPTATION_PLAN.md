# InfinityAI.Pro - INDIAN MARKET ADAPTATION PLAN & IMPLEMENTATION

**Objective**: Complete adaptation of InfinityAI.Pro from US market (AAPL, MSFT, GOOGL, TSLA) to Indian market (NSE/BSE stocks)

**Current Status**: ✅ Planning Phase

**Date**: 2026-01-19

---

## Part 1: Indian Market Fundamentals

### 1.1 Market Hours & Calendar

```
National Stock Exchange (NSE) - PRIMARY
├─ Trading Hours: 09:15 IST - 15:30 IST (Mon-Fri)
├─ Pre-open: 09:00 - 09:15 IST
├─ Holidays: Republic Day (26 Jan), Independence Day (15 Aug), Gandhi Jayanti (2 Oct), etc.
├─ Settlement: T+2 (Trade date + 2 business days)
└─ Regulated by: SEBI (Securities & Exchange Board of India)

BSE (Bombay Stock Exchange) - SECONDARY
├─ Trading Hours: 09:15 IST - 15:30 IST (same as NSE)
├─ Primary listing for smaller companies
└─ Integration: Optional (most trading on NSE)

Time Zone: IST (Indian Standard Time) = UTC + 5:30 hours
```

### 1.2 Nifty 50 Index Components (Recommended Focus)

**Top 20 Stocks (by market cap)**:

```
1. Reliance Industries (RIL)   - Energy, Telecom, Retail
2. TCS (Tata Consultancy)      - IT Services
3. HDFC Bank (HDFCBANK)        - Banking
4. Infosys (INFY)              - IT Services
5. Bajaj Auto (BAJAJ-AUTO)     - Auto/Motorcycles
6. LT (Larsen & Toubro)        - Construction, Engineering
7. SBI (SBIN)                  - Banking (State Bank)
8. Bharti Airtel (AIRTEL)      - Telecom
9. ITC (ITC)                   - FMCG, Tobacco, Hotels
10. Axis Bank (AXISBANK)       - Banking
11. Wipro (WIPRO)              - IT Services
12. Maruti Suzuki (MARUTI)     - Auto Manufacturing
13. Sun Pharma (SUNPHARMA)     - Pharmaceuticals
14. Nestlé India (NESTLEIND)   - FMCG (Foods)
15. HCL Technologies (HCLTECH) - IT Services
16. Asian Paints (ASIANPAINT)  - Paints & Chemicals
17. Titan Company (TITAN)      - Retail, Jewelry, Watches
18. Tech Mahindra (TECHM)      - IT Services
19. NTPC (NTPC)                - Power Generation
20. Coal India (COALIND)       - Mining

**Key Sectors to Track**:
- IT/Tech: TCS, Infosys, Wipro, HCL, Tech Mahindra
- Banking: HDFC Bank, SBI, Axis Bank, ICICI Bank
- Energy: Reliance, NTPC, Oil & Gas
- Auto: Bajaj Auto, Maruti, Hero MotoCorp, Mahindra
- FMCG: ITC, Nestlé, Britannia
- Pharma: Sun Pharma, Dr. Reddy's, Lupin
- Telecom: Airtel, Jio (Reliance)
```

### 1.3 Key Regulatory Requirements

```
SEBI 2025 Compliance:
├─ Position Limits: Max 2-5% open interest per contract
├─ Circuit Filters: 10% price move triggers automatic halt
├─ Settlement: T+2 mandatory
├─ KYC: Required for all traders
├─ Disclosure: Large position reporting (>2% shareholding)
└─ Risk Management: VaR-based margin calculation

Tax Implications:
├─ Short-term Capital Gains (< 1 year): As per income slab (15-42%)
├─ Long-term Capital Gains (> 1 year): 20% (with indexation benefit)
├─ STT (Securities Transaction Tax): 0.1% buy/sell (equity)
└─ GST: 18% on brokerage fees

Broker Constraints (DHAN):
├─ Leverage: 2-5x for intraday, 1-2x for delivery
├─ Margin: 10-20% of trade value
├─ Daily limits: Position size caps per stock
└─ Order limits: 100-1000 orders/day depending on plan
```

---

## Part 2: Data Provider Mapping

### 2.1 Indian Market Data Providers

```
PRIMARY OPTIONS:

1. NSE Direct API (Recommended)
   ├─ Coverage: Real-time NSE data
   ├─ Symbols: All NSE-listed companies
   ├─ Rate Limit: Varies by tier
   ├─ Cost: Free for basic, paid for real-time
   ├─ Documentation: https://www.nseindia.com/products/content/equities/web_services/nseapi.htm
   └─ Status: Official exchange data - MOST RELIABLE

2. AlphaVantage (Supports India)
   ├─ Symbols: NSE format (e.g., TCS.NSE, INFY.NSE)
   ├─ Rate Limit: 5 req/min (free), 600 req/min (premium)
   ├─ Data: Historical + real-time
   └─ Cost: $0 - $25/mo (ALREADY INTEGRATED)

3. EOD Historical Data (India Support)
   ├─ Symbols: NSE/BSE stocks
   ├─ Rate Limit: 100k/day (paid)
   ├─ Data: Historical, splits, dividends
   └─ Cost: $100+/mo (Not currently used)

4. Finnhub (India Support)
   ├─ Symbols: NSE stocks (.NS suffix)
   ├─ Rate Limit: 60 requests/minute
   ├─ Cost: Free tier + paid
   └─ Status: Alternative real-time source

5. YahooFinance API (Unsupported official)
   ├─ Symbols: NSE/BSE via yfinance Python library
   ├─ Cost: Free, but unofficial (rate limited by Yahoo)
   └─ Risk: Subject to blocking

6. ODIN Data (Indian Broker)
   ├─ Symbols: NSE/BSE real-time
   ├─ Cost: $0-50/mo depending on tier
   └─ Status: Indian company, local support

RECOMMENDATION:
├─ Primary: Use AlphaVantage with NSE symbol format (TCS.NSE, INFY.NSE)
├─ Secondary: Add NSE Direct API for official data
└─ Fallback: Implement yfinance for quotes
```

### 2.2 Indian News Providers

```
PRIMARY OPTIONS:

1. Economic Times (Recommended)
   ├─ Format: RSS feed
   ├─ Coverage: Markets, stocks, companies
   ├─ URL: https://economictimes.indiatimes.com/
   ├─ Sentiment: Financial news for India
   └─ Cost: Free (RSS)

2. Moneycontrol
   ├─ Format: RSS feed
   ├─ Coverage: Stock quotes, markets, analysis
   ├─ URL: https://www.moneycontrol.com/rss/
   ├─ Sentiment: Indian markets focus
   └─ Cost: Free (RSS)

3. LiveMint
   ├─ Format: RSS feed
   ├─ Coverage: Markets, personal finance, analysis
   ├─ URL: https://www.livemint.com/rss/
   ├─ Sentiment: Business & markets
   └─ Cost: Free (RSS)

4. BSE Announcements
   ├─ Format: REST API
   ├─ Coverage: Corporate actions, suspensions, IPOs
   ├─ URL: https://www.bseindia.com/
   └─ Cost: Free API

5. NSE Circulars & Notices
   ├─ Format: Web scraping or RSS
   ├─ Coverage: Market updates, rules, regulations
   ├─ URL: https://www.nseindia.com/
   └─ Cost: Free

6. NewsAPI (with India filter)
   ├─ Symbols: Search "India stocks", "NSE", "SEBI"
   ├─ Coverage: International view of Indian market
   └─ Cost: 100 req/day (free tier - ALREADY INTEGRATED)

7. NewsData.io (with India filter)
   ├─ Countries: India (country code: 'in')
   ├─ Languages: Hindi, English
   └─ Cost: 2k calls/day (free tier - ALREADY INTEGRATED)

RECOMMENDATION:
├─ Primary: RSS feeds (Economic Times, Moneycontrol, LiveMint) - ZERO COST
├─ Secondary: NewsAPI + NewsData.io with India filter (ALREADY INTEGRATED)
├─ Tertiary: Web scraping for BSE/NSE official announcements
└─ Implementation: Create IndianNewsProvider adapter
```

### 2.3 Symbol Mapping Convention

```
NSE SYMBOL FORMAT:
├─ Format: SYMBOL.NSE (e.g., TCS.NSE, INFY.NSE)
├─ Delimiter: Hyphen for multi-word (e.g., BAJAJ-AUTO.NSE)
├─ ISIN: 12-character code (e.g., INE001A01015 for TCS)
└─ Exchange Code: NS (NSE), BO (BSE)

INTERNAL SYMBOL MAPPING (needed for provider compatibility):
├─ AlphaVantage: TCS.NSE
├─ NSE API: TCS (SYMBOL only)
├─ Frontend Display: TCS (with NSE context)
├─ Database: TCS (normalized)
└─ Mapping Config: backend/config/symbol_map.json

EXAMPLE MAPPING TABLE:
{
  "display": "TCS",
  "nse_symbol": "TCS",
  "alphavantage_symbol": "TCS.NSE",
  "isin": "INE001A01015",
  "sector": "IT",
  "market_cap": "14.5T",
  "exchange": "NSE"
}
```

---

## Part 3: Provider Integration Strategy

### 3.1 Adapter Updates Needed

```
✓ MODIFY: backend/shared/providers/alpha_vantage.py
  ├─ Change symbols to NSE format (TCS.NSE instead of AAPL)
  ├─ Update quote parsing for Indian market
  └─ Add IST timezone handling

✓ MODIFY: backend/shared/providers/marketstack.py
  ├─ Add NSE/BSE exchange configuration
  ├─ Handle Indian rupee (INR) pricing
  └─ Update API parameters for Indian data

✓ ADD NEW: backend/shared/providers/nse_api.py
  ├─ Direct NSE API integration
  ├─ Real-time quotes for NSE-listed stocks
  └─ Fast, official data source

✓ MODIFY: backend/shared/providers/newsapi.py
  ├─ Filter for India news
  ├─ Focus on market-relevant keywords
  └─ Add Nifty 50 stock names

✓ MODIFY: backend/shared/providers/newsdataio.py
  ├─ Set country filter to India ('in')
  ├─ Set language to Hindi/English
  └─ Focus on financial news topics

✓ ADD NEW: backend/shared/providers/indian_news.py
  ├─ RSS feed integration (Economic Times, Moneycontrol, LiveMint)
  ├─ RSS parsing for financial news
  ├─ Zero API cost, reliable feeds
  └─ Sentiment analysis for Indian context

✓ MODIFY: backend/shared/providers/models.py
  ├─ Add IST timezone support
  ├─ Add ISIN code field
  ├─ Add sector and market_cap fields
  └─ Add regulatory information fields
```

### 3.2 Configuration Changes

```
✓ Environment Variables (.env):
  MARKET_REGION=INDIA
  MARKET_EXCHANGES=NSE,BSE
  PRIMARY_EXCHANGE=NSE
  MARKET_HOURS_START=09:15
  MARKET_HOURS_END=15:30
  MARKET_TIMEZONE=Asia/Kolkata
  TRADING_CURRENCY=INR

  PROVIDER_ALPHAVANTAGE_MARKET=india
  PROVIDER_NSE_API_KEY=...
  PROVIDER_ECONOMIICTIMES_ENABLED=true
  PROVIDER_MONEYCONTROL_ENABLED=true
  PROVIDER_LIVEMINT_ENABLED=true

✓ Symbol Configuration:
  Create: backend/config/indian_symbols.json
  Contains: All Nifty 50 stocks with NSE codes, ISINs, sectors

✓ Market Configuration:
  Create: backend/config/indian_market_config.json
  Contains: Market hours, holidays, circuit limits, regulations

✓ Timezone Handling:
  Update all providers to use IST (UTC+5:30)
  Update Pub/Sub timestamps to IST
  Update UI to display in IST
```

---

## Part 4: Engine Adaptations

### 4.1 Engine A (Momentum - MACD)

```
MODIFICATIONS:
├─ MACD Parameters:
│  ├─ Current: (12, 26, 9) - works for US stocks
│  ├─ Indian Market: May need (10, 20, 9) for faster moves
│  └─ Volatility: Indian stocks typically higher volatility
│
├─ Threshold Adjustments:
│  ├─ Momentum Strength: Lower thresholds (0.05-0.10 instead of 0.15)
│  ├─ Signal Crossover: Tighter bands for faster response
│  └─ Confirmation: Require volume confirmation (NSE volume data)
│
└─ Risk Adjustment:
   ├─ Position size: Reduce for higher volatility
   ├─ Stop loss: Wider bands (2-3% instead of 1.9%)
   └─ Take profit: Lower targets (3-5% instead of 4.5%)
```

### 4.2 Engine B (Mean Reversion - RSI/BB)

```
MODIFICATIONS:
├─ RSI Parameters:
│  ├─ Current: RSI(14) - standard
│  ├─ Indian Market: RSI(14) still valid, but...
│  ├─ Overbought Threshold: 70 → 75 (Indian stocks peak higher)
│  └─ Oversold Threshold: 30 → 25 (bounce faster)
│
├─ Bollinger Bands Parameters:
│  ├─ Current: (20, 2) - standard
│  ├─ Indian Market: (20, 2.5) for wider bands
│  └─ Rationale: Higher volatility requires wider bands
│
└─ Mean Reversion Signal:
   ├─ Entry: RSI(14) > 75 (sell) or < 25 (buy)
   ├─ Confirmation: Close near upper/lower BB band
   ├─ Position: Reduced size due to volatility
   └─ Stop: Wider than US equities
```

### 4.3 Engine C (ML Composite)

```
MODIFICATIONS:
├─ Training Data:
│  ├─ Current: Trained on US stocks (AAPL, MSFT, GOOGL, TSLA)
│  ├─ Required: Retrain on Indian stock data (TCS, INFY, HDFC, etc.)
│  └─ Data Period: Last 2 years of NSE data
│
├─ Features to Add:
│  ├─ Sector sentiment (Banking vs IT vs Auto)
│  ├─ Nifty 50 index correlation
│  ├─ Rupee vs Dollar movements
│  ├─ India VIX (volatility index)
│  └─ SEBI regulatory announcements
│
├─ Model Updates:
│  ├─ Rebalance feature weights for Indian market
│  ├─ Adjust confidence thresholds
│  ├─ Include seasonal patterns (e.g., earnings calendar)
│  └─ Add holiday/market event handling
│
└─ Output Adjustments:
   ├─ Confidence scores recalibrated
   ├─ Position sizing for Indian volatility
   ├─ Risk-adjusted recommendations
   └─ Sector-specific insights
```

---

## Part 5: Implementation Roadmap

### Phase 1: Core Configuration (Day 1)

- [ ] Create Indian symbol mapping file
- [ ] Create market configuration file
- [ ] Update .env.example for Indian market
- [ ] Document Indian market hours and holidays

### Phase 2: Data Providers (Day 2-3)

- [ ] Update alpha_vantage.py for NSE symbols
- [ ] Update marketstack.py for NSE/BSE
- [ ] Create nse_api.py adapter
- [ ] Create indian_news.py for RSS feeds
- [ ] Update newsapi.py and newsdataio.py filters

### Phase 3: Engine Adaptations (Day 3-4)

- [ ] Update Engine A (MACD) parameters
- [ ] Update Engine B (RSI/BB) parameters
- [ ] Retrain/update Engine C (ML)
- [ ] Update risk models for volatility

### Phase 4: Testing & Verification (Day 4-5)

- [ ] End-to-end test pipeline
- [ ] Test with actual NSE data
- [ ] Backtest signals on historical data
- [ ] Verify timezone handling (IST)

### Phase 5: Documentation & Deployment (Day 5)

- [ ] Create Indian market operations guide
- [ ] Document symbol list and mappings
- [ ] Create deployment checklist
- [ ] Deploy to production

---

## Part 6: Key Considerations & Challenges

### 6.1 Technical Challenges

```
1. Timezone Management:
   Problem: IST (UTC+5:30) ≠ UTC
   Solution: All timestamps converted to IST at ingestion
   Impact: Pub/Sub messages, database records, UI displays

2. Market Hours:
   Problem: NSE closes 15:30 IST (5am UTC during standard time)
   Solution: Adjust Cloud Scheduler jobs for IST market open
   Impact: Scheduler triggers, data ingestion timing

3. Currency Conversion:
   Problem: INR prices, not USD
   Solution: All systems assume INR (no conversion needed for domestic trading)
   Impact: Price parsing, risk calculations, portfolio values

4. Symbol Format Inconsistency:
   Problem: Different providers use different formats
   Solution: Symbol mapper converts TCS ↔ TCS.NSE ↔ INE001A01015
   Impact: Provider integration, database normalization

5. Regulatory Data:
   Problem: NSE/BSE provide additional regulatory data
   Solution: Store ISIN, sector, market cap, circuit limits
   Impact: Risk engine, position sizing, circuit breaker logic
```

### 6.2 Operational Challenges

```
1. Holiday Calendar:
   Problem: Different holidays than US market
   Solution: Maintain Indian market holiday list
   Impact: Scheduler jobs skip holidays, no trading signals

2. Sector Seasonality:
   Problem: Indian market has unique seasonal patterns
   Solution: Adjust ML model for monsoon impact, harvest seasons, etc.
   Impact: Forecast accuracy during seasonal periods

3. News Language:
   Problem: Hindi + English news feeds
   Solution: Translate Hindi sentiment to English for ML
   Impact: News processing, sentiment analysis

4. Volatility Spikes:
   Problem: Indian stocks more volatile than US
   Solution: Wider stop losses, position sizing
   Impact: Risk management, signal thresholds

5. Liquidity Variations:
   Problem: Not all NSE stocks equally liquid
   Solution: Filter for Nifty 50 (most liquid)
   Impact: Order execution, slippage estimation
```

### 6.3 Regulatory & Compliance

```
1. SEBI Position Limits:
   Problem: Max 2-5% of open interest per contract
   Solution: Implement position limit checker
   Impact: Trade rejection if exceeds limits

2. Circuit Filters:
   Problem: 10% price move triggers automatic halt
   Solution: Detect halted stocks, stop trading
   Impact: Risk mitigation, automatic stops

3. Settlement Cycles:
   Problem: T+2 settlement (not T+1)
   Solution: Account for 2-day settlement in cash management
   Impact: Margin calculations, available cash

4. KYC & Tax:
   Problem: Trader must be verified, tax implications
   Solution: Store KYC status, calculate tax liability
   Impact: Account setup, reporting

5. Broker Constraints (DHAN):
   Problem: Leverage limits, daily order limits
   Solution: Configure limits in risk engine
   Impact: Max position size, trade frequency
```

---

## Part 7: Expected Outcomes

### 7.1 Before → After Comparison

```
BEFORE (US Market):
┌─────────────────────────────────────────────────┐
│ Stocks: AAPL, MSFT, GOOGL, TSLA, SPY            │
│ Providers: Alpha Vantage, MarketStack, Massive  │
│ News: NewsAPI (40k+ global sources)             │
│ Market Hours: 09:30-16:00 EST                   │
│ Trading Hours: 24/5 (forex-like)                │
│ Broker: Dhan (Indian broker)                    │
│ Base Currency: USD                              │
│ Timezone: EST/UTC                               │
│ Signals: AAPL BUY @$234.50                      │
└─────────────────────────────────────────────────┘

AFTER (Indian Market):
┌─────────────────────────────────────────────────┐
│ Stocks: TCS, INFY, HDFC, RIL, BAJAJ, etc        │
│ Providers: NSE API, Alpha Vantage (NSE), EOD    │
│ News: Economic Times, Moneycontrol, LiveMint    │
│ Market Hours: 09:15-15:30 IST                   │
│ Trading Hours: Same as NSE (live)               │
│ Broker: Dhan (native Indian broker)             │
│ Base Currency: INR                              │
│ Timezone: IST (UTC+5:30)                        │
│ Signals: TCS BUY @₹3,500 (IST timezone)         │
└─────────────────────────────────────────────────┘
```

### 7.2 Market Analysis Example (Indian Market)

```
MARKET ANALYSIS: 2026-01-19 (IST)

TCS (Tata Consultancy Services):
├─ Current Price: ₹3,500
├─ Signals:
│  ├─ Engine A (MACD): BULLISH (+0.85)
│  ├─ Engine B (RSI): NEUTRAL (48.5)
│  └─ Engine C (ML): BULLISH (+0.88)
├─ Composite: BUY
├─ Entry: ₹3,500
├─ Target: ₹3,675 (+5%)
└─ Stop: ₹3,400 (-2.9%)

Infosys (INFY):
├─ Current Price: ₹1,950
├─ Signals:
│  ├─ Engine A (MACD): BULLISH (+0.82)
│  ├─ Engine B (RSI): OVERBOUGHT (72)
│  └─ Engine C (ML): HOLD (+0.70)
├─ Composite: HOLD (trimming overbought position)
├─ Target: ₹2,100 (+7.7%)
└─ Stop: ₹1,850 (-5.1%)

HDFC Bank (HDFCBANK):
├─ Current Price: ₹1,650
├─ Signals:
│  ├─ Engine A (MACD): BULLISH (+0.79)
│  ├─ Engine B (RSI): NEUTRAL (55)
│  └─ Engine C (ML): BULLISH (+0.84)
├─ Composite: BUY
├─ Entry: ₹1,650
├─ Target: ₹1,800 (+9.1%)
└─ Stop: ₹1,600 (-3.0%)

Portfolio Allocation:
├─ TCS: 3.5%
├─ INFY: 2.5% (trimmed from overbought)
├─ HDFC Bank: 4.0%
├─ Nifty 50 ETF: 30%
└─ Cash: 60% (ready for dips)
```

---

## Part 8: Success Criteria

✅ **System is considered successfully adapted when:**

1. ✅ All 7 provider adapters work with Indian symbols
2. ✅ Pub/Sub pipeline ingests NSE data correctly
3. ✅ All 3 engines generate signals for Indian stocks
4. ✅ Market analysis shows Indian stock examples (TCS, INFY, etc.)
5. ✅ Timezone handling is correct (IST throughout)
6. ✅ News providers return Indian market news
7. ✅ Risk models account for Indian market volatility
8. ✅ End-to-end test passes with actual NSE data
9. ✅ Documentation updated for Indian market operations
10. ✅ Deployment verified on production GCP

---

**Status**: Ready for Phase 1 Implementation

**Next Step**: Create Indian Market Configuration Files

---
