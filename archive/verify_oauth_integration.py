#!/usr/bin/env python3
"""
InfinityAI.Pro - OAuth Integration Verification
Verify Dhan OAuth integration is working correctly
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - OAUTH-VERIFICATION - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OAuthVerifier:
    def __init__(self):
        self.engine_c_url = "https://engine-c-573866363639-573866363639.us-central1.run.app"
        self.test_results = {}

    async def verify_oauth_status(self) -> Dict[str, Any]:
        """Verify OAuth status endpoint"""
        logger.info("🔍 Verifying OAuth status endpoint...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.engine_c_url}/api/dhan/status"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        required_fields = [
                            'oauth_active', 'oauth_configured', 
                            'client_id', 'redirect_uri', 'scopes'
                        ]
                        
                        all_fields_present = all(field in data for field in required_fields)
                        oauth_configured = data.get('oauth_configured', False)
                        
                        logger.info(f"✅ OAuth Status: {'Configured' if oauth_configured else 'Not Configured'}")
                        logger.info(f"   Client ID: {data.get('client_id', 'N/A')}")
                        logger.info(f"   Redirect URI: {data.get('redirect_uri', 'N/A')}")
                        logger.info(f"   Scopes: {data.get('scopes', 'N/A')}")
                        
                        return {
                            'status': 'success',
                            'oauth_configured': oauth_configured,
                            'all_fields_present': all_fields_present,
                            'data': data
                        }
                    else:
                        logger.error(f"❌ OAuth status endpoint returned HTTP {response.status}")
                        return {'status': 'failed', 'http_code': response.status}
                        
            except Exception as e:
                logger.error(f"❌ Error checking OAuth status: {e}")
                return {'status': 'error', 'error': str(e)}

    async def verify_oauth_initiate(self) -> Dict[str, Any]:
        """Verify OAuth initiation endpoint"""
        logger.info("🚀 Verifying OAuth initiation endpoint...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.engine_c_url}/api/auth/dhan/initiate"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        required_fields = ['auth_url', 'state', 'redirect_uri', 'client_id']
                        all_fields_present = all(field in data for field in required_fields)
                        
                        auth_url = data.get('auth_url', '')
                        valid_auth_url = 'api.dhan.co' in auth_url and 'client_id=' in auth_url
                        
                        logger.info(f"✅ OAuth Initiation Response:")
                        logger.info(f"   State: {data.get('state', 'N/A')[:16]}...")
                        logger.info(f"   Auth URL: {auth_url[:50]}...")
                        logger.info(f"   Valid URL: {valid_auth_url}")
                        
                        return {
                            'status': 'success',
                            'all_fields_present': all_fields_present,
                            'valid_auth_url': valid_auth_url,
                            'data': data
                        }
                    else:
                        logger.error(f"❌ OAuth initiate returned HTTP {response.status}")
                        text = await response.text()
                        return {'status': 'failed', 'http_code': response.status, 'response': text[:200]}
                        
            except Exception as e:
                logger.error(f"❌ Error testing OAuth initiation: {e}")
                return {'status': 'error', 'error': str(e)}

    async def verify_callback_security(self) -> Dict[str, Any]:
        """Verify callback endpoint security"""
        logger.info("🛡️ Verifying OAuth callback security...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.engine_c_url}/api/dhan/callback"
                
                # Test with malformed data
                malformed_data = {
                    'code': '<script>alert("xss")</script>',
                    'state': 'DROP TABLE oauth;',
                    'redirect_uri': 'http://malicious.com'
                }
                
                async with session.post(url, json=malformed_data) as response:
                    if response.status == 400:
                        logger.info("✅ Callback security: Properly rejects malformed input")
                        return {
                            'status': 'success',
                            'rejects_malformed': True,
                            'security_validated': True
                        }
                    else:
                        logger.warning(f"⚠️ Callback security: Unexpected response {response.status}")
                        return {
                            'status': 'partial',
                            'rejects_malformed': False,
                            'security_validated': False,
                            'http_code': response.status
                        }
                        
            except Exception as e:
                logger.error(f"❌ Error testing callback security: {e}")
                return {'status': 'error', 'error': str(e)}

    async def verify_order_placement_security(self) -> Dict[str, Any]:
        """Verify order placement endpoint security"""
        logger.info("💹 Verifying order placement security...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.engine_c_url}/api/orders/place"
                
                # Test with malicious input
                malicious_order = {
                    'symbol': '<script>alert("xss")</script>',
                    'quantity': -999999,
                    'order_type': 'DROP TABLE orders;',
                    'transaction_type': 'UNION SELECT * FROM users;',
                    'demo': True
                }
                
                async with session.post(url, json=malicious_order) as response:
                    if response.status == 400:
                        data = await response.json()
                        logger.info("✅ Order placement security: Properly validates input")
                        return {
                            'status': 'success',
                            'validates_input': True,
                            'security_response': data
                        }
                    else:
                        logger.warning(f"⚠️ Order placement security: Unexpected response {response.status}")
                        text = await response.text()
                        return {
                            'status': 'partial',
                            'validates_input': False,
                            'http_code': response.status,
                            'response': text[:200]
                        }
                        
            except Exception as e:
                logger.error(f"❌ Error testing order placement security: {e}")
                return {'status': 'error', 'error': str(e)}

    async def verify_security_headers(self) -> Dict[str, Any]:
        """Verify security headers are present"""
        logger.info("🔒 Verifying security headers...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.engine_c_url}/health"
                async with session.get(url) as response:
                    headers = response.headers
                    
                    required_security_headers = {
                        'Strict-Transport-Security': 'HSTS',
                        'Content-Security-Policy': 'CSP',
                        'X-Frame-Options': 'Frame Protection',
                        'X-Content-Type-Options': 'MIME Protection'
                    }
                    
                    present_headers = {}
                    for header, description in required_security_headers.items():
                        if header in headers:
                            present_headers[header] = headers[header]
                            logger.info(f"✅ {description}: Present")
                        else:
                            logger.warning(f"❌ {description}: Missing")
                    
                    security_score = (len(present_headers) / len(required_security_headers)) * 100
                    
                    return {
                        'status': 'success',
                        'security_score': security_score,
                        'present_headers': present_headers,
                        'missing_headers': [h for h in required_security_headers.keys() if h not in present_headers]
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error checking security headers: {e}")
                return {'status': 'error', 'error': str(e)}

    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run comprehensive OAuth integration verification"""
        
        print("🔍 InfinityAI.Pro - OAuth Integration Verification")
        print("=" * 60)
        print(f"Starting verification at {datetime.now().isoformat()}")
        print("=" * 60)
        
        verification_results = {}
        
        # Test 1: OAuth Status
        print("\n🔍 TEST 1: OAuth Status Endpoint")
        print("-" * 40)
        verification_results['oauth_status'] = await self.verify_oauth_status()
        
        # Test 2: OAuth Initiation
        print("\n🚀 TEST 2: OAuth Initiation Endpoint")
        print("-" * 40)
        verification_results['oauth_initiate'] = await self.verify_oauth_initiate()
        
        # Test 3: Callback Security
        print("\n🛡️ TEST 3: OAuth Callback Security")
        print("-" * 40)
        verification_results['callback_security'] = await self.verify_callback_security()
        
        # Test 4: Order Placement Security
        print("\n💹 TEST 4: Order Placement Security")
        print("-" * 40)
        verification_results['order_security'] = await self.verify_order_placement_security()
        
        # Test 5: Security Headers
        print("\n🔒 TEST 5: Security Headers")
        print("-" * 40)
        verification_results['security_headers'] = await self.verify_security_headers()
        
        # Generate summary
        summary = self.generate_verification_summary(verification_results)
        
        return {
            'verification_timestamp': datetime.now().isoformat(),
            'verification_results': verification_results,
            'summary': summary
        }

    def generate_verification_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate verification summary"""
        
        passed_tests = 0
        total_tests = len(results)
        
        oauth_ready = False
        security_ready = False
        
        # Analyze results
        for test_name, test_result in results.items():
            if test_result.get('status') == 'success':
                passed_tests += 1
                
                if test_name == 'oauth_status' and test_result.get('oauth_configured'):
                    oauth_ready = True
                    
                if test_name == 'security_headers' and test_result.get('security_score', 0) >= 75:
                    security_ready = True
        
        success_rate = (passed_tests / total_tests) * 100
        overall_status = 'READY' if success_rate >= 80 and oauth_ready else 'NEEDS_WORK'
        
        print(f"\n" + "=" * 60)
        print("📊 OAUTH INTEGRATION VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {overall_status}")
        print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"OAuth Ready: {'✅ YES' if oauth_ready else '❌ NO'}")
        print(f"Security Ready: {'✅ YES' if security_ready else '❌ NO'}")
        
        recommendations = []
        if not oauth_ready:
            recommendations.append("🔧 Complete OAuth configuration with valid client credentials")
        if not security_ready:
            recommendations.append("🛡️ Implement additional security headers")
        if success_rate < 100:
            recommendations.append("🔍 Fix failing verification tests")
            
        if recommendations:
            print(f"\n📋 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        else:
            print(f"\n🎉 All verifications passed! OAuth integration is ready.")
        
        return {
            'overall_status': overall_status,
            'success_rate': success_rate,
            'oauth_ready': oauth_ready,
            'security_ready': security_ready,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'recommendations': recommendations
        }

async def main():
    """Main verification function"""
    
    verifier = OAuthVerifier()
    
    try:
        verification_report = await verifier.run_comprehensive_verification()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"oauth_verification_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(verification_report, f, indent=2, default=str)
        
        print(f"\n📄 Verification report saved: {filename}")
        
        return verification_report
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())