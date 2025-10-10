#!/usr/bin/env python3
"""
🤖 Dhan API Auto-Token Refresh Service
🔄 Automatically refreshes Dhan access tokens daily
⚡ Runs as background service or scheduled task
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time
import sys

class DhanAutoTokenRefresh:
    """Automated Dhan API token refresh service"""

    def __init__(self, config_file="dhan_credentials_secure.json", log_file="dhan_token_refresh.log"):
        self.config_file = Path(config_file)
        self.log_file = Path(log_file)
        self.setup_logging()

        # Dhan API endpoints
        self.auth_url = "https://api.dhan.co/login"  # For token generation
        self.base_url = "https://api.dhan.co"

        # Load existing credentials
        self.credentials = self.load_credentials()

    def setup_logging(self):
        """Setup logging for the service"""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Also log to console
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        self.logger = logging.getLogger(__name__)

    def load_credentials(self):
        """Load existing credentials from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load credentials: {e}")
                return {}
        return {}

    def save_credentials(self, credentials):
        """Save updated credentials to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
            self.logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")
            return False

    def generate_access_token(self, api_key, api_secret):
        """Generate new access token using API key and secret"""
        try:
            payload = {
                "api_key": api_key,
                "api_secret": api_secret
            }
            headers = {'Content-Type': 'application/json'}

            self.logger.info("Generating new access token...")
            response = requests.post(self.auth_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            access_token = data.get('access_token')

            if access_token:
                self.logger.info("✅ Access token generated successfully")
                return access_token
            else:
                self.logger.error("❌ No access token in response")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Network error generating token: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error generating token: {e}")
            return None

    def validate_token(self, access_token, client_id):
        """Validate if the current token is still working"""
        try:
            # Try a simple API call to validate the token
            url = f"{self.base_url}/v2/marketfeed/ltp"
            headers = {
                'access-token': access_token,
                'client-id': str(client_id),
                'Content-Type': 'application/json'
            }
            payload = {"IDX_I": [13]}  # Test with NIFTY

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                self.logger.info("Token expired (401 Unauthorized)")
                return False
            else:
                self.logger.warning(f"Unexpected validation response: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return False

    def refresh_token_if_needed(self):
        """Check and refresh token if expired or about to expire"""
        if not self.credentials:
            self.logger.error("No credentials found. Please run manual setup first.")
            return False

        client_id = self.credentials.get('client_id')
        api_key = self.credentials.get('api_key')
        api_secret = self.credentials.get('api_secret')
        current_token = self.credentials.get('access_token')
        last_updated = self.credentials.get('last_updated')

        if not all([client_id, api_key, api_secret]):
            self.logger.error("Missing required credentials (client_id, api_key, api_secret)")
            return False

        # Check if token needs refresh (if it's been more than 20 hours or validation fails)
        needs_refresh = False

        if last_updated:
            try:
                last_update_time = datetime.fromisoformat(last_updated)
                hours_since_update = (datetime.now() - last_update_time).total_seconds() / 3600
                if hours_since_update > 20:  # Refresh if older than 20 hours
                    needs_refresh = True
                    self.logger.info(f"Token is {hours_since_update:.1f} hours old, refreshing...")
            except:
                needs_refresh = True
                self.logger.info("Could not parse last update time, refreshing token...")

        # Validate current token if we have one
        if current_token and not needs_refresh:
            if not self.validate_token(current_token, client_id):
                needs_refresh = True
                self.logger.info("Current token validation failed, refreshing...")

        if needs_refresh:
            # Generate new token
            new_token = self.generate_access_token(api_key, api_secret)
            if new_token:
                # Update credentials
                self.credentials['access_token'] = new_token
                self.credentials['last_updated'] = datetime.now().isoformat()

                # Save to file
                if self.save_credentials(self.credentials):
                    # Update main application config
                    self.update_application_config()
                    self.logger.info("✅ Token refresh completed successfully")
                    return True
                else:
                    self.logger.error("❌ Failed to save updated credentials")
                    return False
            else:
                self.logger.error("❌ Failed to generate new token")
                return False
        else:
            self.logger.info("✅ Token is still valid, no refresh needed")
            return True

    def update_application_config(self):
        """Update the main application configuration with new token"""
        try:
            app_config_file = Path("nifty_options_analysis.py")

            if not app_config_file.exists():
                self.logger.warning("Main application config file not found")
                return False

            # Read current config
            with open(app_config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update access token in the config
            old_token = self.credentials.get('access_token')
            if old_token:
                # Find and replace the token (look for the pattern in the config)
                import re
                token_pattern = r'"access_token":\s*"[^"]*"'
                new_token_line = f'"access_token": "{old_token}"'

                if re.search(token_pattern, content):
                    content = re.sub(token_pattern, new_token_line, content)

                    # Write back
                    with open(app_config_file, 'w', encoding='utf-8') as f:
                        f.write(content)

                    self.logger.info("✅ Main application config updated")
                    return True
                else:
                    self.logger.warning("Could not find access token pattern in config")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to update application config: {e}")
            return False

    def run_service(self, interval_hours=4):
        """Run as a continuous service checking tokens periodically"""
        self.logger.info("🚀 Starting Dhan API Auto-Token Refresh Service")
        self.logger.info(f"📊 Check interval: {interval_hours} hours")
        self.logger.info("Press Ctrl+C to stop the service")

        try:
            while True:
                self.logger.info("🔄 Checking token status...")
                success = self.refresh_token_if_needed()

                if success:
                    self.logger.info(f"✅ Token check completed. Next check in {interval_hours} hours.")
                else:
                    self.logger.error("❌ Token refresh failed. Will retry in next cycle.")

                # Wait for next check
                time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            self.logger.info("🛑 Service stopped by user")
        except Exception as e:
            self.logger.error(f"Service error: {e}")
            sys.exit(1)

    def run_once(self):
        """Run a single token refresh check"""
        self.logger.info("Running one-time token refresh check...")
        success = self.refresh_token_if_needed()

        if success:
            print("SUCCESS: Token refresh completed successfully")
            return True
        else:
            print("FAILED: Token refresh failed")
            return False

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Dhan API Auto-Token Refresh Service")
    parser.add_argument("--service", action="store_true", help="Run as continuous service")
    parser.add_argument("--interval", type=int, default=4, help="Check interval in hours (default: 4)")
    parser.add_argument("--config", default="dhan_credentials_secure.json", help="Credentials config file")
    parser.add_argument("--log", default="dhan_token_refresh.log", help="Log file")

    args = parser.parse_args()

    # Create service instance
    service = DhanAutoTokenRefresh(args.config, args.log)

    if args.service:
        # Run as continuous service
        service.run_service(args.interval)
    else:
        # Run one-time check
        success = service.run_once()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()