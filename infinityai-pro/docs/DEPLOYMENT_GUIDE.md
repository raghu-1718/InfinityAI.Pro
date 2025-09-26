# InfinityAI.Pro Complete Deployment Guide

## 📋 Your Configuration Details

### 🔑 Credentials (Already Configured)
- **Dhan Client ID**: `1101302170`
- **Telegram Bot Token**: `8207295165:AAF8xjybeADYLLXZ-GZrQwoYzvF0JrgmMU8`
- **Telegram Chat ID**: `7946285735`
- **Business Email**: `raghuyuvi10@gmail.com`
- **Private Email**: `chotu@infinityai.pro`
- **Business Phone**: `+91856936854`

### ☁️ Azure Subscription Details
- **Subscription ID**: `62fc147a-2efc-4494-be1f-faa521439799`
- **Subscription Name**: `Azure_Infinity.AI`
- **Directory**: `Default Directory (raghuyuvi10gmail.onmicrosoft.com)`
- **Role**: `Owner`
- **Status**: `Active`

### 🌐 Domain Information
- **Domain**: `infinityai.pro`
- **Private Email Plan**: Pro (Active until Nov 14, 2025)
- **Email Storage**: 30GB available
- **Spam Filter**: Jellyfish enabled

---

## 🚀 Step-by-Step Deployment

### Step 1: Azure Authentication
```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription 62fc147a-2efc-4494-be1f-faa521439799

# Verify login
az account show
```

### Step 2: Create Azure Resources
```bash
# Create resource group
az group create --name infinityai-pro-rg --location eastus

# Create DNS zone
az network dns zone create --resource-group infinityai-pro-rg --name infinityai.pro

# Get Azure nameservers
az network dns zone show --resource-group infinityai-pro-rg --name infinityai.pro --query nameServers
```

### Step 3: Update Namecheap Nameservers
1. Go to Namecheap → Domain List → infinityai.pro
2. Click "Nameservers" in the left menu
3. Select "Custom DNS"
4. Enter the Azure nameservers from Step 2
5. Save changes

**Wait 4-24 hours for DNS propagation**

### Step 4: Configure Private Email DNS Records
```bash
# Run the DNS setup script
./setup-dns.sh
```

This configures:
- **MX Records**: `mx1.privateemail.com`, `mx2.privateemail.com`
- **SPF Record**: `v=spf1 include:spf.privateemail.com ~all`

### Step 5: Set Up DKIM (Manual)
1. Go to Namecheap → infinityai.pro → Private Email
2. Click "DKIM" section
3. Copy the selector and value
4. Run in terminal:
```bash
# Replace SELECTOR and VALUE with your DKIM details
az network dns record-set txt create \
  --resource-group infinityai-pro-rg \
  --zone-name infinityai.pro \
  --name 'YOUR_SELECTOR._domainkey' \
  --value 'YOUR_DKIM_VALUE'
```

### Step 6: Deploy to Azure Container Apps
```bash
# Run the deployment script
cd azure/container-apps
./deploy-infinityai.sh
```

### Step 7: Configure SendGrid (Optional)
```bash
# Visit https://sendgrid.com
# Sign up and verify raghuyuvi10@gmail.com
# Create API key
export SENDGRID_API_KEY="your_sendgrid_api_key"
```

### Step 8: Configure Twilio (Optional)
```bash
# Visit https://twilio.com
# Sign up and verify +91856936854
# Enable WhatsApp
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_NUMBER="+91856936854"
```

---

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://infinityai.pro/health
curl https://infinityai.pro/health/detailed
```

### Notification Testing
```bash
# Test Telegram
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "telegram", "message": "Test from InfinityAI.Pro"}'

# Test WhatsApp (if configured)
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "whatsapp", "message": "Test WhatsApp"}'

# Test Email (if SendGrid configured)
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "email", "message": "Test Email"}'
```

### Email Testing
```bash
# Send test email to your private email
echo "Test email from InfinityAI.Pro" | mail -s "Test Subject" chotu@infinityai.pro
```

---

## 📊 Monitoring & Maintenance

### Check Notification Status
```bash
curl https://infinityai.pro/health/notification-status
```

### View Logs
```bash
# Container app logs
az containerapp logs show \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --follow
```

### Update Deployment
```bash
# Rebuild and redeploy
cd azure/container-apps
./deploy-infinityai.sh
```

---

## 🔧 Troubleshooting

### DNS Issues
```bash
# Check DNS propagation
nslookup infinityai.pro
nslookup -type=MX infinityai.pro
nslookup -type=TXT infinityai.pro
```

### Email Issues
- Check DKIM setup in Namecheap
- Verify SPF record: `dig TXT infinityai.pro`
- Test MX records: `dig MX infinityai.pro`

### Azure Issues
```bash
# Check container app status
az containerapp show \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --query provisioningState
```

---

## 📞 Support Contacts

- **Domain**: Namecheap support
- **Private Email**: Namecheap Private Email support
- **Azure**: Microsoft Azure support
- **SendGrid**: SendGrid documentation
- **Twilio**: Twilio documentation
- **Dhan API**: Dhan trading API documentation

---

## 🎯 Success Checklist

- [ ] Azure account configured
- [ ] Resource group created
- [ ] DNS zone created
- [ ] Namecheap nameservers updated
- [ ] DNS records configured (MX, SPF, DKIM)
- [ ] Container app deployed
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Health endpoints responding
- [ ] Telegram notifications working
- [ ] Email system tested
- [ ] WhatsApp configured (optional)

**Your InfinityAI.Pro trading platform is now ready for production! 🚀**