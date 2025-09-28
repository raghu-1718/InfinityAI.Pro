#!/bin/bash
# Dhan Static IP Setup Script
# Run this to get your current IP and setup instructions

echo "🔍 Dhan Static IP Setup Assistant"
echo "=================================="
echo ""

# Get current public IP
echo "📡 Detecting your current public IP..."
CURRENT_IP=$(curl -s ifconfig.me)
echo "Your current IP: $CURRENT_IP"
echo ""

# Check if it's static or dynamic
echo "🔍 IP Analysis:"
echo "Note: If this IP changes when you restart your router,"
echo "you have a DYNAMIC IP and need a STATIC IP from your ISP."
echo ""

# Provide setup instructions
echo "📋 Dhan Static IP Setup Steps:"
echo "=================================="
echo ""
echo "1. Login to Dhan Web Platform:"
echo "   https://web.dhan.co"
echo ""
echo "2. Navigate to:"
echo "   DhanHQ Trading APIs → Setup Static IP"
echo ""
echo "3. Click 'Add New IP' or 'Setup Static IP'"
echo ""
echo "4. Enter your static IP address:"
echo "   IP Address: $CURRENT_IP"
echo "   Description: InfinityAI.Pro Trading Server"
echo ""
echo "5. Click 'Save' or 'Whitelist'"
echo ""
echo "6. Verify status shows 'Active' or 'Whitelisted'"
echo ""

# Check if IP is from common cloud providers
if [[ $CURRENT_IP =~ ^(3\.|34\.|35\.|52\.|54\.) ]]; then
    echo "☁️  Detected: AWS IP range"
    echo "💡 Tip: Use Elastic IP for static address"
elif [[ $CURRENT_IP =~ ^(13\.|20\.|40\.|104\.) ]]; then
    echo "☁️  Detected: Azure IP range"  
    echo "💡 Tip: Use Static Public IP"
elif [[ $CURRENT_IP =~ ^(138\.68\.|134\.209\.|159\.89\.|104\.248\.) ]]; then
    echo "☁️  Detected: DigitalOcean IP range"
    echo "💡 Tip: Use Reserved IP ($6/month)"
else
    echo "🏠 Detected: Residential/ISP IP"
    echo "💡 Contact your ISP for static IP service"
fi

echo ""
echo "⚠️  IMPORTANT:"
echo "- Static IP whitelisting is MANDATORY after October 1st, 2025"
echo "- Only one IP can be whitelisted per Dhan account"
echo "- Test API calls from the whitelisted IP only"
echo ""

# Update .env file
echo "🔧 Updating your .env file with current IP..."
cd backend
if [ -f ".env" ]; then
    # Backup original
    cp .env .env.backup
    
    # Update or add DHAN_STATIC_IP
    if grep -q "DHAN_STATIC_IP=" .env; then
        sed -i "s/DHAN_STATIC_IP=.*/DHAN_STATIC_IP=$CURRENT_IP/" .env
    else
        echo "DHAN_STATIC_IP=$CURRENT_IP" >> .env
    fi
    echo "✅ .env file updated with IP: $CURRENT_IP"
else
    echo "❌ .env file not found"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Complete static IP whitelisting in Dhan dashboard"
echo "2. Test authentication: python test_dhan_auth.py"
echo "3. Run full setup: python setup_dhan_api_2025.py"
