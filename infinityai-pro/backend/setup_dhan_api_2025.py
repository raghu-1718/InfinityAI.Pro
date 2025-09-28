#!/usr/bin/env python3
"""
DhanHQ API Migration Setup Script - October 2025
Helps migrate from legacy authentication to new API key + TOTP system
"""

import os
import json
import base64
import qrcode
import pyotp
from pathlib import Path
from dotenv import load_dotenv

# Load current environment
load_dotenv()

def setup_static_ip():
    """Guide user through static IP setup"""
    print("🔧 STATIC IP WHITELISTING SETUP")
    print("=" * 50)
    print("⚠️  IMPORTANT: Static IP whitelisting is REQUIRED after October 1st, 2025")
    print()
    print("Steps to get a static IP:")
    print("1. Contact your ISP (Airtel, Jio, BSNL, etc.)")
    print("2. Request a static IP address (costs ₹500-2000/month)")
    print("3. Configure it on your router/firewall")
    print("4. Test connectivity from that IP")
    print()
    print("Alternative: Use cloud static IP (AWS, Azure, DigitalOcean)")
    print("- AWS: Elastic IP (free tier eligible)")
    print("- Azure: Static Public IP")
    print("- DigitalOcean: Reserved IP")
    print()

    static_ip = input("Enter your static IP address (leave empty to skip): ").strip()
    if static_ip:
        # Update .env file
        env_file = Path(".env")
        content = env_file.read_text()

        if "DHAN_STATIC_IP=" in content:
            content = content.replace("DHAN_STATIC_IP=your_static_ip_address_here", f"DHAN_STATIC_IP={static_ip}")
        else:
            content += f"\nDHAN_STATIC_IP={static_ip}"

        env_file.write_text(content)
        print(f"✅ Static IP configured: {static_ip}")
        return static_ip
    else:
        print("⚠️  Static IP not configured - required for production trading")
        return None

def setup_api_key_auth():
    """Setup new API key authentication"""
    print("\n🔑 API KEY AUTHENTICATION SETUP")
    print("=" * 50)
    print("The new DhanHQ API uses API keys instead of access tokens.")
    print()
    print("To get API keys:")
    print("1. Login to Dhan Web Platform: https://web.dhan.co")
    print("2. Go to: DhanHQ Trading APIs → API Keys")
    print("3. Click 'Create New API Key'")
    print("4. Set permissions (read, trade)")
    print("5. Valid for 12 months")
    print()

    api_key = input("Enter your Dhan API Key: ").strip()
    api_secret = input("Enter your Dhan API Secret: ").strip()

    if api_key and api_secret:
        # Update .env file
        env_file = Path(".env")
        content = env_file.read_text()

        content = content.replace("DHAN_API_KEY=your_dhan_api_key_here", f"DHAN_API_KEY={api_key}")
        content = content.replace("DHAN_API_SECRET=your_dhan_api_secret_here", f"DHAN_API_SECRET={api_secret}")

        env_file.write_text(content)
        print("✅ API key authentication configured")
        return api_key, api_secret
    else:
        print("❌ API key setup incomplete")
        return None, None

def setup_totp_auth():
    """Setup TOTP authentication for 2FA"""
    print("\n🔢 TOTP 2FA AUTHENTICATION SETUP")
    print("=" * 50)
    print("DhanHQ now requires TOTP (Time-based One-Time Password) for API authentication.")
    print()
    print("To setup TOTP:")
    print("1. Install Google Authenticator or Authy app")
    print("2. Go to Dhan Web → Settings → Security → 2FA")
    print("3. Enable TOTP and scan the QR code")
    print("4. The app will show the secret key - copy it")
    print()

    setup_totp = input("Do you want to setup TOTP now? (y/n): ").strip().lower()

    if setup_totp == 'y':
        totp_secret = input("Enter your TOTP secret key: ").strip()

        if totp_secret:
            # Validate TOTP secret
            try:
                import pyotp
                totp = pyotp.TOTP(totp_secret)
                test_code = totp.now()
                print(f"✅ TOTP configured - test code: {test_code}")

                # Update .env file
                env_file = Path(".env")
                content = env_file.read_text()
                content = content.replace("DHAN_TOTP_SECRET=your_dhan_totp_secret_here", f"DHAN_TOTP_SECRET={totp_secret}")
                env_file.write_text(content)

                print("✅ TOTP authentication configured")
                return totp_secret

            except Exception as e:
                print(f"❌ TOTP validation failed: {e}")
                return None
        else:
            print("❌ TOTP secret not provided")
            return None
    else:
        print("⚠️  TOTP setup skipped - required for API authentication")
        return None

def test_authentication(api_key, api_secret, totp_secret, static_ip):
    """Test the new authentication system"""
    print("\n🧪 TESTING NEW AUTHENTICATION SYSTEM")
    print("=" * 50)

    try:
        from services.broker_dhan import DhanAdapter

        adapter = DhanAdapter(
            api_key=api_key,
            api_secret=api_secret,
            totp_secret=totp_secret,
            static_ip=static_ip
        )

        # Test authentication
        token = adapter.authenticate_with_api_key()

        if token:
            print("✅ Authentication successful!")
            print(f"🔑 Access token obtained (valid for 24 hours)")

            # Test token validity check
            is_valid = adapter.ensure_valid_token()
            print(f"🔄 Token validity check: {'✅ Valid' if is_valid else '❌ Invalid'}")

            return True
        else:
            print("❌ Authentication failed")
            print("💡 Check your API credentials and TOTP setup")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def generate_migration_report():
    """Generate a migration status report"""
    print("\n📊 DHANHQ API MIGRATION REPORT")
    print("=" * 50)

    # Check current configuration
    api_key = os.getenv("DHAN_API_KEY")
    api_secret = os.getenv("DHAN_API_SECRET")
    totp_secret = os.getenv("DHAN_TOTP_SECRET")
    static_ip = os.getenv("DHAN_STATIC_IP")

    # Legacy credentials (being phased out)
    legacy_token = os.getenv("DHAN_ACCESS_TOKEN")
    legacy_client = os.getenv("DHAN_CLIENT_ID")

    report = {
        "migration_status": "IN_PROGRESS",
        "new_authentication": {
            "api_key_configured": bool(api_key and api_key != "your_dhan_api_key_here"),
            "api_secret_configured": bool(api_secret and api_secret != "your_dhan_api_secret_here"),
            "totp_configured": bool(totp_secret and totp_secret != "your_dhan_totp_secret_here"),
            "static_ip_configured": bool(static_ip and static_ip != "your_static_ip_address_here")
        },
        "legacy_authentication": {
            "access_token_configured": bool(legacy_token),
            "client_id_configured": bool(legacy_client)
        },
        "compliance_status": {
            "static_ip_whitelisting": "REQUIRED after Oct 1st, 2025",
            "token_validity": "24 hours maximum",
            "authentication_method": "API key + TOTP preferred"
        }
    }

    # Calculate completion percentage
    new_auth_items = sum(report["new_authentication"].values())
    total_auth_items = len(report["new_authentication"])
    completion_pct = (new_auth_items / total_auth_items) * 100

    report["completion_percentage"] = completion_pct

    if completion_pct == 100:
        report["migration_status"] = "COMPLETE"
        print("🎉 MIGRATION COMPLETE - Ready for October 2025 API changes!")
    elif completion_pct >= 75:
        report["migration_status"] = "NEARLY_COMPLETE"
        print("✅ Almost ready - complete remaining setup")
    else:
        report["migration_status"] = "IN_PROGRESS"
        print("🔄 Migration in progress - complete setup steps")

    print(f"📈 Completion: {completion_pct:.1f}%")
    print()

    # Print detailed status
    print("🔐 New Authentication Status:")
    for item, status in report["new_authentication"].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {item.replace('_', ' ').title()}")

    print("\n📋 Next Steps:")
    if not report["new_authentication"]["static_ip_configured"]:
        print("  1. Setup static IP whitelisting (URGENT - required after Oct 1st)")
    if not report["new_authentication"]["api_key_configured"]:
        print("  2. Configure API key and secret")
    if not report["new_authentication"]["totp_configured"]:
        print("  3. Setup TOTP 2FA authentication")

    if completion_pct == 100:
        print("  ✅ Ready for production trading with new DhanHQ APIs!")

    return report

def main():
    print("🚀 DhanHQ API Migration Setup - October 2025")
    print("=" * 60)
    print("This script helps you migrate to DhanHQ's new authentication system.")
    print("Key changes: API keys, TOTP 2FA, 24hr tokens, static IP whitelisting")
    print()

    # Check if required packages are installed
    try:
        import pyotp
        import qrcode
    except ImportError:
        print("❌ Missing required packages. Install with:")
        print("   pip install pyotp qrcode[pil]")
        return

    # Step 1: Static IP setup
    static_ip = setup_static_ip()

    # Step 2: API key authentication
    api_key, api_secret = setup_api_key_auth()

    # Step 3: TOTP setup
    totp_secret = setup_totp_auth()

    # Step 4: Test authentication
    if api_key and api_secret and totp_secret:
        test_success = test_authentication(api_key, api_secret, totp_secret, static_ip)
        if test_success:
            print("\n🎉 DhanHQ API migration successful!")
        else:
            print("\n⚠️  Authentication test failed - check your credentials")
    else:
        print("\n⚠️  Setup incomplete - some authentication components missing")

    # Step 5: Generate migration report
    report = generate_migration_report()

    print("\n💡 Important Notes:")
    print("• Access tokens are now valid for maximum 24 hours")
    print("• Static IP whitelisting is mandatory after October 1st, 2025")
    print("• API keys are valid for 12 months")
    print("• TOTP is required for all API authentication")
    print("• Legacy access tokens will be phased out")

    print("\n🔗 Useful Links:")
    print("• DhanHQ API Docs: https://dhanhq.co/docs")
    print("• API Key Setup: https://web.dhan.co → DhanHQ Trading APIs")
    print("• Static IP Setup: https://dhanhq.co/docs/static-ip")

if __name__ == "__main__":
    main()
