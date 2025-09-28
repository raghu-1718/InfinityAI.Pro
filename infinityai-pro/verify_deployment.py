#!/usr/bin/env python3
"""
InfinityAI.Pro Production Deployment Verification Script
Run this after deployment to verify all systems are working correctly.
"""

import os
import sys
import time
import requests
import json
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DeploymentVerifier:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8000')
        self.session = requests.Session()
        self.session.timeout = 30

    def check_env_vars(self) -> Tuple[bool, List[str], List[str]]:
        """Check if all required environment variables are set."""
        required_vars = {
            # Core Trading
            "CAPITAL": ["11000.0"],
            "RISK_PER_TRADE_PCT": ["0.03"],
            "PAPER_MODE": ["false", "true"],

            # Azure AI (Primary)
            "AZURE_OPENAI_ENDPOINT": [],
            "AZURE_OPENAI_KEY": [],
            "AZURE_OPENAI_DEPLOYMENT": ["gpt-4o"],
            "AZURE_SPEECH_ENDPOINT": [],
            "AZURE_SPEECH_KEY": [],
            "AZURE_VISION_ENDPOINT": [],
            "AZURE_VISION_KEY": [],
            "AZURE_TEXT_ANALYTICS_ENDPOINT": [],
            "AZURE_TEXT_ANALYTICS_KEY": [],
            "AZURE_ML_ENDPOINT": [],
            "AZURE_ML_KEY": [],

            # AWS AI (Secondary)
            "AWS_ACCESS_KEY_ID": [],
            "AWS_SECRET_ACCESS_KEY": [],
            "AWS_REGION": ["us-east-1"],
            "AWS_BEDROCK_MODEL_ID": ["anthropic.claude-3-5-sonnet-20240620-v1:0"],
            "AWS_S3_BUCKET": ["infinityai-models"],

            # Hugging Face
            "HUGGINGFACE_API_KEY": [],

            # Storage
            "STORAGE_PROVIDER": ["aws", "azure"],

            # Broker
            "BROKER_TYPE": ["dhan", "coinswitch"],
            "DHAN_ACCESS_TOKEN": [],
            "DHAN_CLIENT_ID": [],
        }

        missing_vars = []
        set_vars = []

        print("🔍 Checking Environment Variables...\n")

        for var_name, valid_values in required_vars.items():
            value = os.getenv(var_name)

            if value is None:
                missing_vars.append(var_name)
                print(f"❌ {var_name}: NOT SET")
            else:
                set_vars.append(var_name)
                if valid_values and value not in valid_values:
                    print(f"⚠️  {var_name}: SET (value='{value}') - Expected: {valid_values}")
                else:
                    print(f"✅ {var_name}: SET")

        print(f"\n📊 Summary:")
        print(f"   Set: {len(set_vars)}")
        print(f"   Missing: {len(missing_vars)}")

        if missing_vars:
            print(f"\n❌ Missing Variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print(f"\n💡 Copy missing variables from RENDER_ENV_SETUP.md")

        all_set = len(missing_vars) == 0
        return all_set, missing_vars, set_vars

    def test_health_endpoints(self) -> Dict[str, bool]:
        """Test basic health and status endpoints."""
        tests = {
            'main': '/',
            'health': '/health'
        }

        results = {}

        print("🏥 Testing Health Endpoints...\n")

        for name, endpoint in tests.items():
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)

                if response.status_code == 200:
                    print(f"✅ {name}: {response.status_code}")
                    results[name] = True
                else:
                    print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
                    results[name] = False

            except Exception as e:
                print(f"❌ {name}: ERROR - {str(e)}")
                results[name] = False

        return results

    def test_ai_services(self) -> Dict[str, bool]:
        """Test AI service functionality."""
        tests = {
            'llm_chat': {
                'endpoint': '/ai/llm/chat',
                'method': 'POST',
                'data': {'message': 'Hello AI, analyze NIFTY trend'},
                'expected_keys': ['response', 'provider']
            },
            'sentiment_analysis': {
                'endpoint': '/ai/sentiment/analyze',
                'method': 'POST',
                'data': {'text': 'NIFTY is showing strong bullish momentum'},
                'expected_keys': ['sentiment', 'confidence']
            },
            'signal_generation': {
                'endpoint': '/ai/signal/generate',
                'method': 'POST',
                'data': {
                    'symbol': 'NIFTY',
                    'price_data': {'close': [22000, 22050, 22100, 22150, 22200]}
                },
                'expected_keys': ['signal', 'score']
            },
            'risk_assessment': {
                'endpoint': '/ai/risk/assess',
                'method': 'POST',
                'data': {
                    'symbol': 'NIFTY',
                    'action': 'BUY',
                    'quantity': 50,
                    'price': 22000
                },
                'expected_keys': ['risk_score', 'approved']
            }
        }

        results = {}

        print("🤖 Testing AI Services...\n")

        for name, config in tests.items():
            try:
                url = f"{self.base_url}{config['endpoint']}"
                headers = {'Content-Type': 'application/json'}

                if config['method'] == 'POST':
                    response = self.session.post(url, json=config['data'], headers=headers)
                else:
                    response = self.session.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    # Check if expected keys are present
                    expected_keys = config.get('expected_keys', [])
                    if expected_keys:
                        missing_keys = [key for key in expected_keys if key not in data]
                        if missing_keys:
                            print(f"⚠️  {name}: {response.status_code} - Missing keys: {missing_keys}")
                            results[name] = False
                        else:
                            print(f"✅ {name}: {response.status_code}")
                            results[name] = True
                    else:
                        print(f"✅ {name}: {response.status_code}")
                        results[name] = True
                else:
                    print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
                    results[name] = False

            except Exception as e:
                print(f"❌ {name}: ERROR - {str(e)}")
                results[name] = False

        return results

    def test_trading_endpoints(self) -> Dict[str, bool]:
        """Test trading-related endpoints."""
        tests = {
            'user_profile': '/user/profile',
            'trading_status': '/trading/status',
            'user_login': '/user/login'
        }

        results = {}

        print("📈 Testing Trading Endpoints...\n")

        for name, endpoint in tests.items():
            try:
                url = f"{self.base_url}{endpoint}"
                
                if name == 'user_login':
                    # POST request for login
                    response = self.session.post(url, json={"username": "admin", "password": "password123"})
                else:
                    # GET request for others
                    response = self.session.get(url)

                if response.status_code in [200, 401]:  # 401 is OK if not authenticated
                    print(f"✅ {name}: {response.status_code}")
                    results[name] = True
                else:
                    print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
                    results[name] = False

            except Exception as e:
                print(f"❌ {name}: ERROR - {str(e)}")
                results[name] = False

        return results

    def generate_report(self, env_results: Tuple[bool, List[str], List[str]],
                       health_results: Dict[str, bool],
                       ai_results: Dict[str, bool],
                       trading_results: Dict[str, bool]) -> Dict[str, any]:
        """Generate a comprehensive verification report."""

        env_ok, missing_vars, set_vars = env_results

        total_tests = len(health_results) + len(ai_results) + len(trading_results)
        passed_tests = sum(health_results.values()) + sum(ai_results.values()) + sum(trading_results.values())

        report = {
            'timestamp': time.time(),
            'environment': {
                'status': 'PASS' if env_ok else 'FAIL',
                'set_variables': len(set_vars),
                'missing_variables': len(missing_vars),
                'missing_list': missing_vars
            },
            'health_endpoints': {
                'status': 'PASS' if all(health_results.values()) else 'FAIL',
                'total': len(health_results),
                'passed': sum(health_results.values()),
                'failed': len(health_results) - sum(health_results.values()),
                'details': health_results
            },
            'ai_services': {
                'status': 'PASS' if all(ai_results.values()) else 'FAIL',
                'total': len(ai_results),
                'passed': sum(ai_results.values()),
                'failed': len(ai_results) - sum(ai_results.values()),
                'details': ai_results
            },
            'trading_endpoints': {
                'status': 'PASS' if all(trading_results.values()) else 'FAIL',
                'total': len(trading_results),
                'passed': sum(trading_results.values()),
                'failed': len(trading_results) - sum(trading_results.values()),
                'details': trading_results
            },
            'overall': {
                'status': 'PASS' if env_ok and all(health_results.values()) and all(ai_results.values()) and all(trading_results.values()) else 'FAIL',
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            }
        }

        return report

def main():
    print("🚀 InfinityAI.Pro Production Verification")
    print("=" * 50)

    # Get base URL
    base_url = input("Enter your Render app URL (or press Enter for localhost): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"

    verifier = DeploymentVerifier(base_url)

    print(f"\n🔗 Testing deployment at: {base_url}")
    print("-" * 50)

    # Run all checks
    env_results = verifier.check_env_vars()
    print("\n" + "=" * 50)

    health_results = verifier.test_health_endpoints()
    print("\n" + "=" * 50)

    ai_results = verifier.test_ai_services()
    print("\n" + "=" * 50)

    trading_results = verifier.test_trading_endpoints()
    print("\n" + "=" * 50)

    # Generate report
    report = verifier.generate_report(env_results, health_results, ai_results, trading_results)

    # Display results
    print("📊 VERIFICATION REPORT")
    print("=" * 50)

    print(f"Environment Variables: {report['environment']['status']}")
    print(f"  Set: {report['environment']['set_variables']}")
    print(f"  Missing: {report['environment']['missing_variables']}")

    print(f"\nHealth Endpoints: {report['health_endpoints']['status']}")
    print(f"  Passed: {report['health_endpoints']['passed']}/{report['health_endpoints']['total']}")

    print(f"\nAI Services: {report['ai_services']['status']}")
    print(f"  Passed: {report['ai_services']['passed']}/{report['ai_services']['total']}")

    print(f"\nTrading Endpoints: {report['trading_endpoints']['status']}")
    print(f"  Passed: {report['trading_endpoints']['passed']}/{report['trading_endpoints']['total']}")

    print(f"\n🎯 OVERALL STATUS: {report['overall']['status']}")
    print(f"   Success Rate: {report['overall']['success_rate']}")
    print(f"   Tests Passed: {report['overall']['passed_tests']}/{report['overall']['total_tests']}")

    # Save report
    with open('verification_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("\n💾 Report saved to: verification_report.json")    # Final status
    if report['overall']['status'] == 'PASS':
        print("\n🎉 DEPLOYMENT VERIFICATION PASSED!")
        print("   ✅ All systems operational")
        print("   🚀 Ready for production trading")
    else:
        print("\n❌ DEPLOYMENT VERIFICATION FAILED!")
        print("   Check the issues above and fix them")
        print("   Then run this script again")
        sys.exit(1)

if __name__ == "__main__":
    main()