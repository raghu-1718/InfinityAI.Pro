# 🚀 InfinityAI.Pro - User Onboarding Guide

Complete guide to getting started with InfinityAI.Pro algorithmic trading platform.

**Table of Contents**
1. [Getting Started](#getting-started)
2. [Account Setup](#account-setup)
3. [Connecting DhanHQ](#connecting-dhanq)
4. [Paper Trading](#paper-trading)
5. [Live Trading](#live-trading)
6. [Dashboard Guide](#dashboard-guide)
7. [Troubleshooting](#troubleshooting)
8. [Glossary](#glossary)

---

## Getting Started

### What is InfinityAI.Pro?

InfinityAI.Pro is an **institutional-grade algorithmic trading platform** that:
- 📊 Analyzes market data in real-time
- 🤖 Generates AI-powered trading signals
- 💰 Executes trades automatically (or with your approval)
- 📈 Manages risk intelligently
- 📱 Works on web and mobile

### System Requirements

- **Browser**: Chrome, Firefox, Safari, or Edge (latest version)
- **Internet**: Stable connection (minimum 2 Mbps recommended)
- **Device**: Desktop, laptop, tablet, or smartphone
- **Account**: Google account for authentication

### Access the Platform

1. **Visit**: [https://galvanic-pulsar-482815-h0.web.app](https://galvanic-pulsar-482815-h0.web.app)
2. **Login**: Click "Sign in with Google"
3. **Authenticate**: Complete Google authentication
4. **Dashboard**: You'll see the main trading dashboard

---

## Account Setup

### Step 1: Complete Your Profile

After login, complete your profile:

1. **Dashboard** → **Settings** → **Profile**
2. Fill in:
   - Full Name
   - Email (already pre-filled from Google)
   - Phone Number (optional)
   - Trading Experience Level
3. Click **Save Profile**

### Step 2: Set Trading Preferences

**Dashboard** → **Settings** → **Trading Preferences**

Configure:

| Setting | Options | Default | Notes |
|---------|---------|---------|-------|
| Trading Mode | Paper / Live | Paper | ⚠️ Paper by default for safety |
| Risk Level | Conservative / Moderate / Aggressive | Moderate | Affects position sizing |
| Auto-Execute | On / Off | Off | ⚠️ Requires manual approval |
| Max Position Size | 5% - 25% | 10% | Per-symbol exposure limit |
| Daily Loss Limit | $100 - $10,000 | $500 | Stop trading if exceeded |

### Step 3: Set Notification Preferences

**Dashboard** → **Settings** → **Notifications**

Choose how to receive alerts:
- ✅ Email notifications (for signals, orders, alerts)
- ✅ Push notifications (on mobile app)
- ✅ In-app notifications (live updates)
- ✅ SMS notifications (premium feature)

---

## Connecting DhanHQ

### Why Connect DhanHQ?

DhanHQ is your **broker connection** - it:
- Provides real-time market data
- Executes your trades
- Manages your account balance
- Stores your holdings

### Step 1: Get DhanHQ Credentials

1. **Visit**: [https://dhanhq.co](https://dhanhq.co)
2. **Sign Up**: Create a DhanHQ account
3. **Complete KYC**: Upload ID documents (takes 1-2 hours)
4. **Verify Email**: Check your email for verification link
5. **Get Credentials**:
   - Login to DhanHQ
   - Dashboard → Developer Settings
   - Copy:
     - **Client ID**
     - **API Key**
     - **API Secret**

### Step 2: Configure Developer Application (Important!)

In DhanHQ Developer Settings, set webhooks:

1. **Postback URL** (for order updates):
   ```
   https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/postback
   ```

2. **Redirect URL** (for OAuth login):
   ```
   https://engine-c-3acobgd3qa-uc.a.run.app/api/auth/dhan/success
   ```

3. **Generate Webhook Secret**: Save the secret key (used for verification)

### Step 3: Connect in InfinityAI.Pro

1. **Dashboard** → **Settings** → **Broker Connection**
2. Click **Connect DhanHQ**
3. Enter credentials:
   - **Client ID**: (from DhanHQ)
   - **API Key**: (from DhanHQ)
   - **API Secret**: (from DhanHQ)
4. Click **Verify Connection**
5. ✅ If successful, you'll see:
   ```
   ✅ Connection Verified
   Account Balance: $X,XXX
   ```

### Troubleshooting Connection Issues

**Error: "Invalid Credentials"**
- ❌ Double-check Client ID, API Key, API Secret
- ❌ Ensure DhanHQ account KYC is complete
- ❌ Try logging out and back in

**Error: "Webhook URL Rejected"**
- ❌ Verify you've set the Postback URL in DhanHQ settings
- ❌ Webhook URL must exactly match the one provided

**Error: "Connection Timeout"**
- ❌ Check your internet connection
- ❌ DhanHQ API might be temporarily unavailable
- ❌ Try again in 5 minutes

---

## Paper Trading

### What is Paper Trading?

**Paper trading** = Simulated trading with virtual capital
- ✅ No real money at risk
- ✅ Test strategies safely
- ✅ Learn platform features
- ✅ Perfect for beginners

### Starting Paper Trading

1. **Settings** → **Trading Preferences** → Set to **"Paper Mode"**
2. **Dashboard** shows "📄 PAPER TRADING" badge
3. **Virtual Capital**: $1,000,000 (simulated)

### Paper Trading Example

**Scenario**: Buy NIFTY for testing

1. **Trading** → **Quick Trade**
2. Enter:
   - **Symbol**: NIFTY
   - **Quantity**: 1
   - **Order Type**: MARKET
3. Click **Place Order**
4. ✅ Order filled instantly (simulated)
5. **Portfolio** updates with:
   - Position: NIFTY +1
   - Entry Price: (current market price)
   - P&L: (starting at $0)

### Paper Trading Features

| Feature | Availability | Notes |
|---------|--------------|-------|
| Buy/Sell Orders | ✅ Yes | Filled instantly at market price |
| Limit Orders | ✅ Yes | Simulates fills realistically |
| Stop-Loss Orders | ✅ Yes | Triggers automatically |
| Multi-Leg Strategies | ✅ Yes | Test complex strategies |
| P&L Tracking | ✅ Yes | Real-time P&L updates |
| Statistics | ✅ Yes | Win rate, Sharpe ratio, etc. |

### Paper Trading Best Practices

1. **Start Small**: Place 1-2 orders to learn the flow
2. **Try Different Strategies**: Test risk management
3. **Monitor Positions**: Watch how P&L evolves
4. **Use Signals**: Let AI recommend trades, you decide
5. **Review Results**: Check statistics before going live

### Example: Paper Trading Workflow

```
1. [09:15 AM] Market opens
2. [09:16 AM] Signal: Buy NIFTY (80% confidence)
3. [09:17 AM] You review and approve
4. [09:17 AM] Paper order placed: BUY 1 NIFTY @ 19,250
5. [10:00 AM] NIFTY rises to 19,270
6. [10:00 AM] Your P&L: +₹20 (or +0.1%)
7. [02:30 PM] Market hours end
8. [02:31 PM] You sell: SELL 1 NIFTY @ 19,260
9. [02:31 PM] Final P&L: +₹10 (WIN ✅)
```

---

## Live Trading

### ⚠️ IMPORTANT: Before Going Live

**Live trading with real capital is risky. Ensure you:**

1. ✅ Have successfully paper traded for at least 5 days
2. ✅ Understand all risk management features
3. ✅ Have reviewed your trading strategy thoroughly
4. ✅ Start with a **small capital amount** ($500-$1000)
5. ✅ Have read all terms and conditions

### Enabling Live Mode

1. **Settings** → **Trading Preferences** → Change to **"Live Mode"**
2. **Confirmation Dialog**: 
   ```
   ⚠️ WARNING: You are switching to LIVE TRADING
   - Real capital will be at risk
   - Orders will execute on DhanHQ broker
   - Losses are real
   
   Do you want to continue?
   ```
3. Click **"Yes, Enable Live Trading"**
4. ✅ Dashboard now shows "💰 LIVE TRADING" badge

### First Live Trade (Recommended)

**Start with a test trade to verify everything works:**

1. **Capital**: Start with $500-$1000
2. **Symbol**: NIFTY (most liquid)
3. **Quantity**: 1 lot (minimal exposure)
4. **Order**: BUY 1 NIFTY
5. Monitor for:
   - ✅ Order appears in DhanHQ account
   - ✅ Position shows in InfinityAI.Pro portfolio
   - ✅ Real-time P&L updates
6. **Exit**: Sell the same day to test exit flow

### Live Trading Safety Features

InfinityAI.Pro has built-in protections:

| Feature | Function | Example |
|---------|----------|---------|
| **Daily Loss Limit** | Stops trading if daily loss exceeded | Stop at -$500 |
| **Max Position Size** | Limits per-symbol exposure | Max 10% per symbol |
| **Concentration Risk** | Prevents over-concentration | Max 30% in index |
| **Order Confirmation** | Requires your approval (if enabled) | Manual click to execute |
| **Circuit Breaker** | Auto stops on market crash | If market -10% |
| **Emergency Stop** | Instant kill switch | Red button on dashboard |

### Live Trading Workflow

```
1. [09:15 AM] Market opens - Live mode active
2. [09:16 AM] Signal: Buy BANKNIFTY (85% confidence)
3. [09:17 AM] You review signal details
4. [09:17 AM] Click "EXECUTE" (or auto-execute if enabled)
5. [09:17 AM] ✅ Order sent to DhanHQ
6. [09:17 AM] ✅ Order confirmed by broker
7. [09:17 AM] Portfolio updates with real position
8. [10:00 AM] Real P&L tracking begins
9. [02:30 PM] You exit or AI auto-exits
10. [02:31 PM] Trade completed - check realized P&L
```

### Daily Risk Checklist

Before market opens (9:00 AM IST):

- [ ] Check daily loss limit counter (reset? under limit?)
- [ ] Verify trading mode (Paper or Live?)
- [ ] Check DhanHQ account balance
- [ ] Review any overnight news/gaps
- [ ] Ensure internet connection is stable
- [ ] Test emergency stop button

---

## Dashboard Guide

### Main Dashboard Layout

```
┌─────────────────────────────────────────────┐
│  Header: Logo | Welcome, [Name] | Settings  │
├─────────────────────────────────────────────┤
│                                             │
│ ┌─ Portfolio Summary ────────────────────┐ │
│ │ Balance: $95,000                       │ │
│ │ Invested: $50,000                      │ │
│ │ Cash: $45,000                          │ │
│ │ P&L: +$5,000 (+5.6%)                   │ │
│ └────────────────────────────────────────┘ │
│                                             │
│ ┌─ Active Positions ────────────────────┐ │
│ │ Symbol | Qty | Entry | Current | P&L │ │
│ │ NIFTY  | 1   | 19250 | 19,280  | +30 │ │
│ │ GOLD   | 5   | 6500  | 6,480   | -100│ │
│ └────────────────────────────────────────┘ │
│                                             │
│ ┌─ Recent Signals ──────────────────────┐ │
│ │ [09:16] BANKNIFTY - Buy (85%) ✅     │ │
│ │ [08:45] FINNIFTY - Hold (60%) ⏳    │ │
│ └────────────────────────────────────────┘ │
│                                             │
│ [Quick Trade] [View All Signals] [Settings]│
└─────────────────────────────────────────────┘
```

### Key Dashboard Sections

#### 1. Portfolio Summary
Shows your total account health:
- **Balance**: Total account value
- **Invested**: Capital in open positions
- **Cash**: Available to trade
- **P&L**: Total profit/loss

**Buttons**:
- **Deposit**: Add money (DhanHQ)
- **Withdraw**: Withdraw profits (DhanHQ)

#### 2. Active Positions
Lists all open trades:
- **Symbol**: What you're holding
- **Qty**: Number of shares/lots
- **Entry**: Your purchase price
- **Current**: Current market price
- **P&L**: Unrealized profit/loss

**Actions per position**:
- **Add**: Buy more
- **Exit**: Close position
- **SL/Target**: Set stop-loss / take-profit

#### 3. Recent Signals
AI trading recommendations:
- **Time**: When signal was generated
- **Symbol**: Which security
- **Signal**: BUY, SELL, or HOLD
- **Confidence**: 0-100% confidence level
- **Status**: ✅ (executed), ⏳ (pending), ❌ (rejected)

**Actions**:
- **View Details**: See reasoning
- **Execute**: Place the trade now
- **Ignore**: Skip this signal

#### 4. Trading Controls
- **Quick Trade**: Manually place order
- **Auto-Trade**: Enable/disable automation
- **Emergency Stop**: Kill all positions instantly
- **View All**: Expand to full view

---

## Settings & Preferences

### General Settings

**Settings** → **General**

- **Theme**: Light / Dark mode
- **Language**: English / Hindi / etc.
- **Time Zone**: Auto-detect or manual
- **24h Format**: ON/OFF

### Trading Settings

**Settings** → **Trading**

- **Trading Mode**: Paper / Live (⚠️ Use Paper first!)
- **Risk Level**: Conservative / Moderate / Aggressive
- **Auto-Execute**: ON/OFF (auto-execute AI signals?)
- **Max Position Size**: 5-25% (per symbol exposure)
- **Daily Loss Limit**: Max loss before stopping
- **Stop-Loss Default**: Where to place SL by default
- **Take-Profit Default**: Where to place TP by default

### Broker Settings

**Settings** → **Broker**

- **DhanHQ Status**: Connected / Disconnected
- **Account Balance**: Live balance from DhanHQ
- **Disconnect**: Revoke InfinityAI.Pro access

### Notification Settings

**Settings** → **Notifications**

Turn notifications ON/OFF for:
- ✅ New trading signals
- ✅ Order executed
- ✅ Position closed
- ✅ Price alerts (custom levels)
- ✅ Daily P&L summary
- ✅ Risk warnings

---

## Troubleshooting

### Common Issues & Solutions

#### "Dashboard Won't Load"
**Symptom**: Blank screen or infinite loading

**Solutions**:
1. Refresh page: `Ctrl+R` (or `Cmd+R`)
2. Clear cache: Settings → Clear Browsing Data
3. Try incognito mode
4. Check internet connection
5. Try different browser

#### "DhanHQ Connection Failed"
**Symptom**: Can't connect broker or getting 401 errors

**Solutions**:
1. Verify credentials in Settings
2. Ensure DhanHQ account KYC is complete
3. Check if API keys are still valid (regenerate if needed)
4. Whitelist InfinityAI.Pro in DhanHQ settings
5. Contact DhanHQ support if issue persists

#### "Paper Trading Orders Won't Fill"
**Symptom**: Orders stuck in pending status

**Solutions**:
1. Verify Market is open (9:15 AM - 3:30 PM IST, Mon-Fri)
2. For limit orders, ensure price is reasonable
3. Try placing a MARKET order instead
4. Refresh page and try again

#### "Paper vs Live Mode Confusion"
**Symptom**: Not sure which mode I'm in

**Check**:
- Look at dashboard badge:
  - 📄 = Paper mode (safe, simulated)
  - 💰 = Live mode (real money)
- View in Settings → Trading → Trading Mode

#### "Signals Not Appearing"
**Symptom**: No BUY/SELL signals shown

**Possible Causes**:
1. Market conditions don't match strategy
2. All signals might be HOLD (wait mode)
3. Your confidence threshold is too high
4. Engine B is offline (check health)

**Fix**:
1. Check signal filter in Dashboard
2. Adjust risk level (might generate more signals)
3. Restart browser
4. Contact support if signals don't return in 1 hour

#### "Lost Connection / App Crashed"
**Symptom**: App suddenly stops responding

**Quick Recovery**:
1. Refresh page immediately (Ctrl+R)
2. Your positions are safe (stored in Firestore)
3. Orders in progress are safe (DhanHQ has them)
4. Check Dashboard - everything should still be there
5. If positions missing, logout and login again

### Emergency Procedures

**MARKET CRASH or MAJOR LOSS**

1. **Immediate**: Click **Emergency Stop** (red button)
   - All positions closed instantly
   - Stops further execution
2. **Check**: View Firestore for trade history
3. **Contact**: Email support@infinityai.pro with details
4. **Review**: What happened? Any system issues?

**BROKER DISCONNECTION**

1. Check internet connection
2. Reconnect DhanHQ: Settings → Broker → Reconnect
3. Verify DhanHQ website is up (https://dhanhq.co)
4. If still down, contact DhanHQ support
5. Your positions are safe (held by broker)

---

## Glossary

### Trading Terms

| Term | Definition | Example |
|------|-----------|---------|
| **BUY** | Go long - buy to profit from price increase | BUY 1 NIFTY |
| **SELL** | Go short - sell to profit from price decrease | SELL 1 NIFTY |
| **HOLD** | Do nothing - wait for better signal | HOLD (0% confidence) |
| **MARKET Order** | Buy/sell at current market price (instant) | Market order fills now |
| **LIMIT Order** | Buy/sell at specified price or better | Wait for price to reach level |
| **STOP-LOSS** | Automatic exit if price drops (loss limit) | SL at -₹500 |
| **TAKE-PROFIT** | Automatic exit if price rises (profit target) | TP at +₹1000 |
| **POSITION** | Active trade - currently holding security | LONG 1 NIFTY |
| **P&L** | Profit & Loss - your gain or loss | +₹500 (profit) or -₹200 (loss) |
| **INTRADAY** | Trade opened and closed same day | Buy 9:15 AM, Sell 3:30 PM |
| **SWING** | Trade held overnight or multi-day | Hold for 3-5 days |
| **PORTFOLIO** | All your combined positions | Total of all holdings |
| **EXPOSURE** | Total capital at risk | If buying NIFTY with $10K, exposure = $10K |
| **SLIPPAGE** | Difference between expected and actual fill price | Order at ₹100, filled at ₹100.50 (₹0.50 slippage) |
| **VOLATILITY** | How much price moves | High vol = big swings = risky |

### Platform Terms

| Term | Definition |
|------|-----------|
| **Engine-A** | Risk management & portfolio optimization engine |
| **Engine-B** | AI signal generation (using ML models) |
| **Engine-C** | Trade execution engine (connects to DhanHQ) |
| **DhanHQ** | Your broker - executes real trades |
| **Firestore** | Secure cloud database (stores your data) |
| **OAuth** | Secure login method (using Google account) |
| **API** | Connection between InfinityAI.Pro and DhanHQ |
| **Webhook** | Real-time update from DhanHQ (order fills, etc.) |
| **HMAC** | Security verification for webhooks (prevents fraud) |

### AI/ML Terms

| Term | Definition |
|------|-----------|
| **Signal** | AI recommendation to BUY, SELL, or HOLD |
| **Confidence** | How sure the AI is (0-100%) |
| **Model** | Mathematical algorithm (e.g., XGBoost) |
| **Ensemble** | Multiple AI models voting together |
| **Backtest** | Testing strategy on historical data |
| **Overfitting** | Model works on past data but fails in real trading |
| **Win Rate** | % of trades that make money |
| **Sharpe Ratio** | Risk-adjusted return metric (higher = better) |
| **Drawdown** | Largest peak-to-trough loss from peak |
| **ML** | Machine Learning - AI that learns from data |

---

## Getting Help

### Support Channels

- **Email**: support@infinityai.pro
- **Live Chat**: Click chat bubble (bottom right)
- **FAQ**: https://infinityai.pro/faq
- **Documentation**: https://infinityai.pro/docs
- **GitHub Issues**: https://github.com/raghu-1718/InfinityAI.Pro/issues

### What to Include in Support Requests

When reporting an issue, include:
1. **Error Message**: Exact error text
2. **Screenshot**: Visual proof of issue
3. **Steps to Reproduce**: How to recreate the problem
4. **Trading Mode**: Paper or Live?
5. **Browser/Device**: Chrome on Windows 11, Safari on iPad, etc.
6. **Time**: When did this happen (with timezone)?

---

**Last Updated**: January 19, 2026  
**Version**: 1.0  
**Status**: ✅ Live & Ready  

For latest updates, visit: https://github.com/raghu-1718/InfinityAI.Pro/wiki
