# User Onboarding Guide

## How to Connect Your DhanHQ Account to InfinityAI.Pro

**Last Updated:** January 20, 2026
**Estimated Time:** 5 minutes

---

## 📋 Prerequisites

Before you begin, you need:

1. ✅ Active DhanHQ trading account
2. ✅ InfinityAI.Pro account (Firebase login)
3. ✅ Access to DhanHQ dashboard

---

## Step 1: Get Your DhanHQ API Credentials

### 1.1 Log in to DhanHQ

1. Visit [https://dhan.co](https://dhan.co)
2. Log in with your credentials
3. Navigate to your dashboard

### 1.2 Access API Settings

1. Click on **Settings** or **Profile**
2. Look for **API** or **Developer** section
3. Click **Generate API Credentials** or **View API Keys**

### 1.3 Copy Your Credentials

You need **4 pieces of information**:

| Credential       | Description                       | Example                      | Where to Find                  |
| ---------------- | --------------------------------- | ---------------------------- | ------------------------------ |
| **Client ID**    | Your DhanHQ account ID            | `1101302170`                 | API Settings → Client ID       |
| **Access Token** | Authentication token (JWT)        | `eyJ0eXAiOiJKV1QiLCJhbGc...` | API Settings → Generate Token  |
| **API Key**      | Market data API key (optional)    | `b76a41e2`                   | API Settings → Data API Key    |
| **API Secret**   | Market data API secret (optional) | `3b27c08e-797c-40e4-...`     | API Settings → Data API Secret |

**⚠️ Important Notes:**

- Access Token expires periodically - you'll need to regenerate it
- API Key/Secret are optional (only needed for advanced market data features)
- Keep these credentials **secure** - never share them publicly

---

## Step 2: Save Credentials in InfinityAI.Pro

### 2.1 Navigate to Settings

1. Log in to [InfinityAI.Pro](https://infinityai.pro)
2. Click your profile icon (top right)
3. Select **Settings** from the dropdown
4. Go to **DhanHQ Integration** tab

### 2.2 Input Your Credentials

1. Paste **Client ID** into the "Client ID" field
2. Paste **Access Token** into the "Access Token" field
3. **(Optional)** Paste **API Key** into the "API Key" field
4. **(Optional)** Paste **API Secret** into the "API Secret" field

**Visual Guide:**

```
┌─────────────────────────────────────────────────┐
│ DhanHQ Integration Settings                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Client ID *                                    │
│  ┌─────────────────────────────────────────┐   │
│  │ 1101302170                              │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Access Token *                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ eyJ0eXAiOiJKV1QiLCJhbGc...             │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  API Key (Optional - for market data)           │
│  ┌─────────────────────────────────────────┐   │
│  │ b76a41e2                                │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  API Secret (Optional)                          │
│  ┌─────────────────────────────────────────┐   │
│  │ 3b27c08e-797c-40e4-8e80-...            │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  [ Save Credentials ]  [ Test Connection ]      │
└─────────────────────────────────────────────────┘
```

### 2.3 Save and Verify

1. Click **"Save Credentials"** button
2. Wait for verification (5-10 seconds)
3. Look for success message: ✅ **"Credentials saved successfully"**

**What Happens Behind the Scenes:**

- Your credentials are encrypted with AES-256-GCM
- Stored securely in Firestore (isolated to your account)
- Never exposed in logs or to other users
- Used only for your trading operations

---

## Step 3: Verify Connection

### 3.1 Test Your Connection

1. Click **"Test Connection"** button (or it auto-tests after save)
2. Wait for verification results

**Expected Results:**

```
✅ Connection Status: Connected
✅ Funds Retrieved: ₹25,000.50 available
✅ Positions Loaded: 3 active positions
✅ DhanHQ API: Responding normally
```

### 3.2 Check Dashboard

1. Navigate to **Dashboard** (home page)
2. Verify you see:
   - Your account funds
   - Current positions
   - Available margin
   - Trading history

---

## Step 4: Start Trading

### 4.1 Your Credentials Are Active

Once saved and verified:

- ✅ All trading uses your DhanHQ account
- ✅ Funds/positions reflect your broker account
- ✅ Orders placed in your name
- ✅ Credentials encrypted and secure

### 4.2 Available Features

With connected DhanHQ account, you can:

- 📊 View live market data
- 💰 Check funds and margin
- 📈 Monitor positions and orders
- 🤖 Use AI trading signals
- 📱 Execute trades (buy/sell)
- 📉 Track portfolio performance

---

## 🔒 Security & Privacy

### Your Credentials Are Safe

- **Encryption:** AES-256-GCM (military-grade)
- **Storage:** Firestore with strict access rules
- **Access:** Only you and backend services
- **Logs:** Never logged or exposed
- **Isolation:** Cannot be accessed by other users

### Best Practices

1. ✅ Use strong Firebase password
2. ✅ Enable 2FA on DhanHQ account
3. ✅ Regenerate Access Token periodically
4. ✅ Never share credentials with anyone
5. ✅ Log out when using shared computers

---

## 🆘 Troubleshooting

### Issue 1: "Invalid Credentials" Error

**Symptoms:** Red error message after clicking "Save"

**Possible Causes:**

- Incorrect Client ID or Access Token
- Expired Access Token
- Extra whitespace when copy/pasting

**Solutions:**

1. Double-check credentials in DhanHQ dashboard
2. Regenerate Access Token if expired
3. Copy/paste carefully (no extra spaces)
4. Try "Test Connection" button

---

### Issue 2: "Connection Failed" Error

**Symptoms:** Cannot verify DhanHQ connection

**Possible Causes:**

- DhanHQ API temporarily down
- Network connectivity issues
- Firewall blocking API calls

**Solutions:**

1. Wait 1 minute and try again
2. Check DhanHQ status page
3. Try from different network
4. Contact support if persists

---

### Issue 3: Credentials Saved but No Data Showing

**Symptoms:** Settings shows "Connected" but Dashboard is empty

**Possible Causes:**

- New account with no trades yet
- DhanHQ account not activated
- Credentials saved but not verified

**Solutions:**

1. Click "Refresh" on Dashboard
2. Verify DhanHQ account is active
3. Check "Test Connection" in Settings
4. Log out and log back in

---

### Issue 4: Need to Update Credentials

**Symptoms:** Access Token expired or changed

**Steps to Update:**

1. Get new Access Token from DhanHQ
2. Go to Settings → DhanHQ Integration
3. Paste new Access Token
4. Click "Save Credentials" (overwrites old one)
5. Verify with "Test Connection"

---

## ❓ FAQ

### Q: Do I need to save credentials every time I log in?

**A:** No! Credentials are saved permanently (until you delete them). Just log in and start trading.

---

### Q: What if I have multiple DhanHQ accounts?

**A:** Each InfinityAI.Pro user can connect one DhanHQ account. Use different InfinityAI.Pro accounts for different broker accounts.

---

### Q: Are API Key and API Secret required?

**A:** No, they're optional. Required only for advanced market data features. Basic trading works with just Client ID and Access Token.

---

### Q: How do I disconnect my DhanHQ account?

**A:** Go to Settings → DhanHQ Integration → Click "Disconnect" or "Delete Credentials". This removes your credentials from the system.

---

### Q: Can InfinityAI.Pro place trades without my permission?

**A:** No! All trades require your explicit action (clicking "Buy" or "Sell"). AI signals are advisory only.

---

### Q: What happens if my Access Token expires?

**A:** Trading will fail with "Authentication Error". Simply regenerate the token in DhanHQ and update in Settings.

---

### Q: Can support staff see my credentials?

**A:** No! Credentials are encrypted. Support can see "Connected" status but never the actual tokens/keys.

---

## 📞 Need Help?

### Support Channels

- **Email:** support@infinityai.pro
- **Discord:** [InfinityAI.Pro Community](https://discord.gg/infinityai)
- **Documentation:** [docs.infinityai.pro](https://docs.infinityai.pro)
- **GitHub Issues:** [github.com/raghu-1718/InfinityAI.Pro/issues](https://github.com/raghu-1718/InfinityAI.Pro/issues)

### Before Contacting Support

Please have ready:

- Your InfinityAI.Pro user ID (from Settings → Account)
- Screenshot of error message (if any)
- Steps you've already tried
- **DO NOT** share actual credentials (we'll never ask for them)

---

## ✅ Checklist

Use this checklist to verify successful onboarding:

- [ ] DhanHQ account active and accessible
- [ ] Client ID copied from DhanHQ dashboard
- [ ] Access Token generated and copied
- [ ] API Key/Secret copied (if using market data)
- [ ] Logged into InfinityAI.Pro
- [ ] Navigated to Settings → DhanHQ Integration
- [ ] Pasted all credentials
- [ ] Clicked "Save Credentials"
- [ ] Saw success message ✅
- [ ] Tested connection successfully
- [ ] Dashboard showing funds/positions
- [ ] Ready to trade! 🚀

---

**Congratulations!** Your DhanHQ account is now connected to InfinityAI.Pro. Happy trading! 📈
