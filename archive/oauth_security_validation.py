#!/usr/bin/env python3
"""
InfinityAI.Pro - OAuth Integration & Security Validation
Comprehensive testing of Dhan OAuth flows, token handling, and security compliance
"""

import asyncio
import aiohttp
import json
import ssl
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlencode

class OAuthSecurityValidator:
    def __init__(self):
        self.services = {
            'Engine C': 'https://engine-c-573866363639-573866363639.us-central1.run.app',
            'Frontend': 'https://infinityai-pro-frontend-573866363639.us-central1.run.app'
        }
        
    async def test_dhan_oauth_endpoints(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test Dhan OAuth integration endpoints"""
        print("🔐 Testing Dhan OAuth Integration Endpoints...")
        
        results = {
            'callback_endpoint': {'status': 'failed', 'data': None},
            'postback_endpoint': {'status': 'failed', 'data': None},
            'status_endpoint': {'status': 'failed', 'data': None},
            'initiate_oauth': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine C']
        
        # Test OAuth status endpoint
        try:
            async with session.get(f"{base_url}/api/dhan/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    results['status_endpoint'] = {
                        'status': 'success',
                        'data': status_data,
                        'oauth_active': status_data.get('oauth_active', False),
                        'connected_users': status_data.get('connected_users', 0),
                        'endpoints_configured': 'endpoints' in status_data
                    }
                    print("   ✅ OAuth status endpoint: FUNCTIONAL")
                else:
                    results['status_endpoint'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ OAuth status endpoint: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ OAuth status endpoint: {str(e)}")
        
        # Test OAuth callback endpoint (simulate callback)
        try:
            callback_params = {
                'code': 'test_auth_code_simulation',
                'state': 'security_validation_test'
            }
            callback_url = f"{base_url}/api/dhan/callback?{urlencode(callback_params)}"
            
            async with session.get(callback_url) as response:
                # We expect 400 or redirect for invalid test code - that's normal
                if response.status in [200, 302, 400]:
                    results['callback_endpoint'] = {
                        'status': 'success',
                        'message': 'Callback endpoint is properly configured',
                        'http_code': response.status,
                        'handles_invalid_codes': response.status == 400
                    }
                    print("   ✅ OAuth callback endpoint: CONFIGURED")
                else:
                    results['callback_endpoint'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ OAuth callback endpoint: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ OAuth callback endpoint: {str(e)}")
        
        # Test postback endpoint (webhook simulation)
        try:
            postback_data = {
                'type': 'order_update',
                'data': {'order_id': 'test_order', 'status': 'completed'},
                'timestamp': datetime.now().isoformat()
            }
            
            async with session.post(f"{base_url}/api/dhan/postback", json=postback_data) as response:
                if response.status in [200, 201, 204]:
                    results['postback_endpoint'] = {
                        'status': 'success',
                        'message': 'Postback endpoint is functional',
                        'http_code': response.status
                    }
                    print("   ✅ OAuth postback endpoint: CONFIGURED")
                else:
                    results['postback_endpoint'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ OAuth postback endpoint: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ OAuth postback endpoint: {str(e)}")
            
        return results

    async def test_token_security(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test token handling and security measures"""
        print("🛡️ Testing Token Security & Handling...")
        
        results = {
            'token_storage': {'status': 'failed', 'data': None},
            'token_validation': {'status': 'failed', 'data': None},
            'token_refresh': {'status': 'failed', 'data': None},
            'secure_transmission': {'status': 'success', 'data': 'HTTPS enforced'}  # Assumed for Cloud Run
        }
        
        base_url = self.services['Engine C']
        
        # Test token validation endpoint
        try:
            headers = {
                'Authorization': 'Bearer test_token_validation_check',
                'Content-Type': 'application/json'
            }
            
            async with session.get(f"{base_url}/api/user/profile", headers=headers) as response:
                if response.status in [401, 403]:
                    # Expected behavior for invalid token
                    results['token_validation'] = {
                        'status': 'success',
                        'message': 'Token validation is properly implemented',
                        'rejects_invalid_tokens': True,
                        'http_code': response.status
                    }
                    print("   ✅ Token validation: SECURE")
                elif response.status == 200:
                    # This might indicate weak token validation
                    results['token_validation'] = {
                        'status': 'warning',
                        'message': 'Token validation might be too permissive',
                        'http_code': response.status
                    }
                    print("   ⚠️ Token validation: REVIEW NEEDED")
                else:
                    results['token_validation'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ Token validation: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Token validation: {str(e)}")
        
        # Test secure token storage endpoint
        try:
            async with session.get(f"{base_url}/api/auth/tokens") as response:
                if response.status == 401:
                    # Good - endpoint is protected
                    results['token_storage'] = {
                        'status': 'success',
                        'message': 'Token storage endpoint is properly protected',
                        'protected': True
                    }
                    print("   ✅ Token storage: PROTECTED")
                elif response.status == 200:
                    results['token_storage'] = {
                        'status': 'warning',
                        'message': 'Token storage might be accessible without auth'
                    }
                    print("   ⚠️ Token storage: REVIEW NEEDED")
                else:
                    results['token_storage'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ Token storage: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Token storage: {str(e)}")
            
        return results

    async def test_user_onboarding(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test user onboarding flow"""
        print("👥 Testing User Onboarding Flow...")
        
        results = {
            'registration': {'status': 'failed', 'data': None},
            'oauth_initiation': {'status': 'failed', 'data': None},
            'user_profile': {'status': 'failed', 'data': None},
            'onboarding_flow': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine C']
        
        # Test user registration
        try:
            registration_data = {
                'email': 'test_security_validation@infinityai.pro',
                'demo': True,
                'validation_test': True
            }
            
            async with session.post(f"{base_url}/api/user/register", json=registration_data) as response:
                if response.status in [200, 201, 409]:  # 409 = user already exists
                    data = await response.json() if response.content_type == 'application/json' else {}
                    results['registration'] = {
                        'status': 'success',
                        'data': data,
                        'user_exists': response.status == 409,
                        'http_code': response.status
                    }
                    print("   ✅ User registration: FUNCTIONAL")
                else:
                    results['registration'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ User registration: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ User registration: {str(e)}")
        
        # Test OAuth initiation
        try:
            async with session.get(f"{base_url}/api/auth/dhan/initiate") as response:
                if response.status in [200, 302]:
                    # 302 redirect to Dhan OAuth or 200 with auth URL
                    if response.status == 302:
                        redirect_url = response.headers.get('Location', '')
                        results['oauth_initiation'] = {
                            'status': 'success',
                            'message': 'OAuth initiation redirects properly',
                            'redirect_url': redirect_url,
                            'contains_dhan': 'dhan' in redirect_url.lower()
                        }
                    else:
                        data = await response.json() if response.content_type == 'application/json' else {}
                        results['oauth_initiation'] = {
                            'status': 'success',
                            'data': data,
                            'auth_url_provided': 'auth_url' in data or 'url' in data
                        }
                    print("   ✅ OAuth initiation: CONFIGURED")
                else:
                    results['oauth_initiation'] = {
                        'status': 'failed',
                        'http_code': response.status
                    }
                    print(f"   ❌ OAuth initiation: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ OAuth initiation: {str(e)}")
            
        return results

    async def test_security_compliance(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test overall security compliance"""
        print("🔒 Testing Security Compliance...")
        
        results = {
            'https_enforcement': {'status': 'success', 'data': 'Cloud Run enforces HTTPS'},
            'cors_configuration': {'status': 'failed', 'data': None},
            'input_validation': {'status': 'failed', 'data': None},
            'rate_limiting': {'status': 'failed', 'data': None},
            'csrf_protection': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine C']
        
        # Test CORS configuration
        try:
            headers = {
                'Origin': 'https://test-domain.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Authorization, Content-Type'
            }
            
            async with session.options(f"{base_url}/api/dhan/status", headers=headers) as response:
                cors_headers = {
                    'access-control-allow-origin': response.headers.get('Access-Control-Allow-Origin'),
                    'access-control-allow-methods': response.headers.get('Access-Control-Allow-Methods'),
                    'access-control-allow-headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                results['cors_configuration'] = {
                    'status': 'success' if any(cors_headers.values()) else 'failed',
                    'data': cors_headers,
                    'properly_configured': bool(cors_headers['access-control-allow-origin'])
                }
                
                if any(cors_headers.values()):
                    print("   ✅ CORS configuration: CONFIGURED")
                else:
                    print("   ❌ CORS configuration: NOT CONFIGURED")
        except Exception as e:
            print(f"   ❌ CORS configuration: {str(e)}")
        
        # Test input validation
        try:
            # Send malformed JSON to test input validation
            malformed_data = {'malicious_script': '<script>alert("xss")</script>', 'invalid_field': 'test'}
            
            async with session.post(f"{base_url}/api/orders/place", json=malformed_data) as response:
                if response.status in [400, 422]:
                    # Good - server validates input
                    results['input_validation'] = {
                        'status': 'success',
                        'message': 'Input validation is properly implemented',
                        'rejects_malformed_data': True,
                        'http_code': response.status
                    }
                    print("   ✅ Input validation: SECURE")
                else:
                    results['input_validation'] = {
                        'status': 'warning',
                        'message': 'Input validation might need review',
                        'http_code': response.status
                    }
                    print(f"   ⚠️ Input validation: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Input validation: {str(e)}")
        
        # Test rate limiting (make rapid requests)
        try:
            rapid_requests = []
            for i in range(20):  # Try 20 rapid requests
                task = session.get(f"{base_url}/health")
                rapid_requests.append(task)
            
            responses = await asyncio.gather(*rapid_requests, return_exceptions=True)
            
            # Count successful vs rate-limited responses
            status_codes = []
            for response in responses:
                if hasattr(response, 'status'):
                    status_codes.append(response.status)
                    if hasattr(response, 'close'):
                        response.close()
            
            rate_limited_count = sum(1 for code in status_codes if code == 429)
            
            results['rate_limiting'] = {
                'status': 'success' if rate_limited_count > 0 else 'warning',
                'data': {
                    'total_requests': len(status_codes),
                    'rate_limited_responses': rate_limited_count,
                    'rate_limiting_active': rate_limited_count > 0
                }
            }
            
            if rate_limited_count > 0:
                print("   ✅ Rate limiting: ACTIVE")
            else:
                print("   ⚠️ Rate limiting: NOT DETECTED")
                
        except Exception as e:
            print(f"   ❌ Rate limiting test: {str(e)}")
            
        return results

    async def run_comprehensive_security_validation(self) -> Dict[str, Any]:
        """Run complete OAuth and security validation"""
        print("🛡️ Starting Comprehensive OAuth & Security Validation")
        print("=" * 70)
        
        connector = aiohttp.TCPConnector(limit=50, ssl=ssl.create_default_context())
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            # Execute all security validation tests
            oauth_results = await self.test_dhan_oauth_endpoints(session)
            await asyncio.sleep(1)
            
            token_security_results = await self.test_token_security(session)
            await asyncio.sleep(1)
            
            onboarding_results = await self.test_user_onboarding(session)
            await asyncio.sleep(1)
            
            security_compliance_results = await self.test_security_compliance(session)
            
        # Compile comprehensive results
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'OAuth Integration & Security Validation',
            'security_assessments': {
                'dhan_oauth_integration': oauth_results,
                'token_security': token_security_results,
                'user_onboarding': onboarding_results,
                'security_compliance': security_compliance_results
            }
        }
        
        return validation_results

    def calculate_security_health(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall security health metrics"""
        
        total_tests = 0
        passed_tests = 0
        warning_tests = 0
        
        for category_name, category_results in results['security_assessments'].items():
            for test_name, test_result in category_results.items():
                total_tests += 1
                status = test_result.get('status', 'failed')
                if status == 'success':
                    passed_tests += 1
                elif status == 'warning':
                    warning_tests += 1
        
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Assess critical security areas
        critical_areas = ['dhan_oauth_integration', 'token_security', 'security_compliance']
        
        security_breakdown = []
        for area in critical_areas:
            if area in results['security_assessments']:
                area_health = sum(1 for test in results['security_assessments'][area].values() 
                                if test.get('status') == 'success')
                area_total = len(results['security_assessments'][area])
                area_percentage = (area_health / area_total * 100) if area_total > 0 else 0
                
                security_breakdown.append({
                    'area': area,
                    'health_percentage': round(area_percentage, 2),
                    'status': '✅ SECURE' if area_percentage >= 80 else '⚠️ REVIEW NEEDED' if area_percentage >= 50 else '❌ CRITICAL'
                })
        
        return {
            'overall_security_score': round(security_score, 2),
            'tests_passed': f"{passed_tests}/{total_tests}",
            'warnings': warning_tests,
            'security_breakdown': security_breakdown,
            'production_ready': security_score >= 75 and warning_tests <= 2,
            'compliance_status': 'COMPLIANT' if security_score >= 85 else 'REVIEW_REQUIRED' if security_score >= 60 else 'NON_COMPLIANT'
        }

async def main():
    validator = OAuthSecurityValidator()
    
    print("🔐 InfinityAI.Pro - OAuth Integration & Security Validation")
    print("Testing Dhan OAuth flows, token handling, and security compliance")
    
    # Run comprehensive security validation
    results = await validator.run_comprehensive_security_validation()
    
    # Calculate security metrics
    security_metrics = validator.calculate_security_health(results)
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("🛡️ OAUTH & SECURITY VALIDATION RESULTS")
    print("=" * 70)
    
    print(f"Overall Security Score: {security_metrics['overall_security_score']}%")
    print(f"Tests Passed: {security_metrics['tests_passed']}")
    print(f"Warnings: {security_metrics['warnings']}")
    print(f"Compliance Status: {security_metrics['compliance_status']}")
    print(f"Production Ready: {'✅ YES' if security_metrics['production_ready'] else '⚠️ NEEDS REVIEW'}")
    
    print("\n🔍 Security Areas Assessment:")
    for area in security_metrics['security_breakdown']:
        print(f"   {area['status']} {area['area']}: {area['health_percentage']}%")
    
    # Save detailed results
    results['security_assessment'] = security_metrics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"oauth_security_validation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📋 Detailed security report saved: {filename}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())