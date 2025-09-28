# Dhan Static IP Setup Guide

## Step-by-Step Static IP Configuration

### 1. Access Dhan Dashboard
1. Login to https://web.dhan.co
2. Navigate to **DhanHQ Trading APIs** section
3. Click on **Setup Static IP**

### 2. Add Your Static IP
1. Click **"Add New IP"** or **"Setup Static IP"**
2. Enter your static IP address
3. Add a description (e.g., "InfinityAI.Pro Trading Server")
4. Click **Save** or **Whitelist**

### 3. Verify IP Whitelisting
1. Check the status shows as "Active" or "Whitelisted"
2. Test with a simple API call to verify

### 4. Update InfinityAI.Pro Configuration
Once IP is whitelisted, update your `.env` file:

```bash
DHAN_STATIC_IP=your.static.ip.address
```

## Getting a Static IP Address

### Option 1: From Your ISP
- Contact your Internet Service Provider (Airtel, Jio, BSNL, etc.)
- Request a **Static IP address**
- Cost: ₹500-2000 per month
- Setup time: 1-3 days

### Option 2: Cloud Static IP (Recommended)
Use free/paid static IPs from cloud providers:

#### AWS (Free Tier Eligible)
```bash
# Create Elastic IP (free for first year)
aws ec2 allocate-address --domain vpc
# Associate with your EC2 instance
aws ec2 associate-address --instance-id i-1234567890abcdef0 --allocation-id eipalloc-12345678
```

#### Azure (Free Static IP)
```bash
# Create static public IP
az network public-ip create \
  --resource-group infinityai-rg \
  --name infinityai-static-ip \
  --sku Standard \
  --allocation-method Static
```

#### DigitalOcean (Reserved IP - $6/month)
```bash
# Create reserved IP via web interface
# Or use doctl CLI
doctl compute reserved-ip create --region blr1
```

### Option 3: VPN with Static IP
- Use commercial VPN services with dedicated IPs
- Services like Mullvad, AirVPN offer static IPs
- Cost: $5-10/month

## Testing Static IP Setup

### 1. Verify Your Current IP
```bash
curl ifconfig.me
# or
curl icanhazip.com
```

### 2. Test Dhan API with Static IP
```bash
cd infinityai-pro/backend
python -c "
import os
from dotenv import load_dotenv
from services.broker_dhan import DhanAdapter

load_dotenv()

# Test with your static IP
adapter = DhanAdapter(
    api_key=os.getenv('DHAN_API_KEY'),
    api_secret=os.getenv('DHAN_API_SECRET'),
    totp_secret=os.getenv('DHAN_TOTP_SECRET'),
    static_ip=os.getenv('DHAN_STATIC_IP')
)

token = adapter.authenticate_with_api_key()
print('✅ Static IP setup successful!' if token else '❌ Static IP setup failed')
"
```

## Troubleshooting Static IP Issues

### Common Problems:
1. **IP not whitelisted**: Double-check in Dhan dashboard
2. **Dynamic IP**: Ensure you're using a true static IP
3. **VPN/proxy interference**: Disable VPN when testing
4. **Network restrictions**: Check firewall settings

### Verification Steps:
1. Confirm IP is listed in Dhan dashboard
2. Test from the whitelisted IP only
3. Check API response headers for IP validation errors

## Important Notes

- **Deadline**: Static IP whitelisting mandatory after October 1st, 2025
- **Single IP**: Only one IP can be whitelisted per Dhan account
- **Testing Required**: Always test API calls from the whitelisted IP
- **Backup Plan**: Have mobile data as backup during setup

## Support

If you face issues:
1. Check Dhan API documentation: https://dhanhq.co/docs
2. Contact Dhan support: https://dhanhq.co/support
3. Verify IP whitelisting status in dashboard
