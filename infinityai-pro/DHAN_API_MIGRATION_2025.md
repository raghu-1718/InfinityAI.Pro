# DhanHQ API Migration Guide - October 2025

## 🚨 URGENT: API Changes Effective October 1st, 2025

DhanHQ has announced critical API authentication changes that affect all traders using their APIs. This guide helps you migrate InfinityAI.Pro to the new authentication system.

## 📋 Key Changes

### 1. **Access Tokens: 24-Hour Validity Only**
- **Before**: Tokens could be generated for longer periods
- **After**: Maximum 24-hour validity
- **Impact**: More frequent token refresh required

### 2. **New API Key Authentication (Preferred Method)**
- **What**: OAuth-based authentication with API keys
- **Validity**: 12 months
- **Security**: Enhanced with 2FA

### 3. **TOTP 2FA Authentication**
- **Required**: For all API-based logins
- **Method**: Time-based One-Time Password
- **Apps**: Google Authenticator, Authy, etc.

### 4. **Static IP Whitelisting (MANDATORY)**
- **Deadline**: October 1st, 2025
- **Requirement**: All API calls must come from whitelisted static IP
- **Cost**: ₹500-2000/month from ISP

## 🔧 Migration Steps

### Step 1: Get Static IP Address
```bash
# Contact your ISP for static IP
# Or use cloud provider static IP:
# - AWS: Elastic IP (free tier)
# - Azure: Static Public IP  
# - DigitalOcean: Reserved IP
```

### Step 2: Setup API Keys
1. Login to [Dhan Web Platform](https://web.dhan.co)
2. Navigate: **DhanHQ Trading APIs** → **API Keys**
3. Click **"Create New API Key"**
4. Set permissions (read, trade)
5. **Save API Key and Secret securely**

### Step 3: Configure TOTP 2FA
1. Go to **Settings** → **Security** → **2FA**
2. Enable TOTP
3. Scan QR code with authenticator app
4. **Save the secret key** (shown during setup)

### Step 4: Update InfinityAI.Pro Configuration

Update your `.env` file with new credentials:

```bash
# Legacy (being phased out)
DHAN_ACCESS_TOKEN=your_old_token
DHAN_CLIENT_ID=your_client_id

# New API authentication (REQUIRED)
DHAN_API_KEY=your_api_key_here
DHAN_API_SECRET=your_api_secret_here
DHAN_TOTP_SECRET=your_totp_secret_here
DHAN_STATIC_IP=your.static.ip.address

# Token management
DHAN_REFRESH_TOKEN=
```

### Step 5: Whitelist Static IP
1. Login to Dhan Web
2. Go to: **DhanHQ Trading APIs** → **Setup Static IP**
3. Enter your static IP address
4. Save configuration

### Step 6: Test New Authentication

Run the migration script:
```bash
cd infinityai-pro/backend
python setup_dhan_api_2025.py
```

## 🔧 Technical Implementation

### Updated DhanAdapter Class

The `DhanAdapter` has been updated with:

- **OAuth Authentication**: API key + TOTP flow
- **Token Management**: 24-hour validity with auto-refresh
- **Static IP Support**: Required header inclusion
- **Fallback Authentication**: Legacy token support during transition

### New Authentication Flow

```python
# New authentication (preferred)
adapter = DhanAdapter(
    api_key="your_api_key",
    api_secret="your_api_secret", 
    totp_secret="your_totp_secret",
    static_ip="your.static.ip"
)

# Authenticate and get 24-hour token
token = adapter.authenticate_with_api_key()

# Token auto-refresh
adapter.ensure_valid_token()  # Refreshes if expired
```

## 📊 Migration Checklist

- [ ] **Static IP obtained and configured**
- [ ] **API key and secret generated**
- [ ] **TOTP 2FA enabled and secret saved**
- [ ] **`.env` file updated with new credentials**
- [ ] **Static IP whitelisted in Dhan dashboard**
- [ ] **Authentication tested successfully**
- [ ] **Legacy tokens removed (after testing)**

## ⚠️ Critical Deadlines

- **October 1st, 2025**: Static IP whitelisting becomes mandatory
- **Ongoing**: 24-hour token validity enforced
- **Recommended**: Complete migration before September 15th, 2025

## 🆘 Troubleshooting

### Authentication Issues
```bash
# Test authentication
cd infinityai-pro/backend
python -c "
from services.broker_dhan import DhanAdapter
adapter = DhanAdapter(api_key='your_key', api_secret='your_secret', totp_secret='your_totp')
token = adapter.authenticate_with_api_key()
print('Success!' if token else 'Failed')
"
```

### Common Errors

1. **"Static IP not whitelisted"**
   - Solution: Complete IP whitelisting in Dhan dashboard

2. **"Invalid TOTP"**
   - Solution: Check TOTP secret and time sync on device

3. **"API key expired"**
   - Solution: Generate new API key (valid 12 months)

4. **"Token expired"**
   - Solution: System auto-refreshes, check network connectivity

## 📞 Support

- **DhanHQ Support**: https://dhanhq.co/support
- **API Documentation**: https://dhanhq.co/docs
- **Community Forum**: https://forum.dhanhq.co

## 🔄 Migration Status

**Current Status**: Implementation Complete ✅
**Testing**: Required with real credentials
**Production Ready**: After user configuration

---

**⚠️ IMPORTANT**: Complete this migration before October 1st, 2025 to avoid trading disruptions. The new authentication system provides better security and reliability for algorithmic trading.
