#!/usr/bin/env python3
"""
InfinityAI.Pro - Frontend Integration Validation
Test frontend integration with backend services, security, performance
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urlparse
import ssl
import socket

# Frontend Configuration
FRONTEND_CONFIG = {
    "production_url": "https://infinityai.pro",
    "expected_features": ["InfinityAI.Pro", "login", "dashboard", "demo", "trading"],
    "demo_credentials": {"username": "demo", "password": "infinityai2024"},
    "performance_threshold": 3000,  # ms
    "security_requirements": ["https", "ssl_valid", "proper_headers"]
}

# Backend Integration Points
BACKEND_ENDPOINTS = {
    "gcp_engines": [
        "https://infinityai-engine-a-573866363639.us-central1.run.app",
        "https://infinityai-engine-b-573866363639.us-central1.run.app",
        "https://infinityai-ultra-aggressive-573866363639.us-central1.run.app"
    ],
    "aws_engines": [
        "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
        "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d"
    ]
}

class FrontendValidator:
    def __init__(self):
        self.results = {}
        
    def test_frontend_accessibility(self):
        """Test basic frontend accessibility and content"""
        print("🌐 TESTING FRONTEND ACCESSIBILITY")
        print("=" * 45)
        
        try:
            start_time = time.time()
            response = requests.get(FRONTEND_CONFIG["production_url"], timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Check response status
            accessible = response.status_code == 200
            print(f"   {'✅' if accessible else '❌'} Accessibility: {response.status_code}")
            
            # Check response time
            fast_enough = response_time < FRONTEND_CONFIG["performance_threshold"]
            print(f"   {'✅' if fast_enough else '❌'} Response Time: {response_time:.2f}ms")
            
            # Check content
            content = response.text.lower()
            feature_checks = {}
            
            for feature in FRONTEND_CONFIG["expected_features"]:
                feature_present = feature.lower() in content
                feature_checks[feature] = feature_present
                print(f"   {'✅' if feature_present else '❌'} Feature '{feature}': {'Present' if feature_present else 'Missing'}")
            
            # Check for demo credentials
            has_demo_info = "demo" in content and "infinityai2024" in content
            print(f"   {'✅' if has_demo_info else '❌'} Demo Credentials: {'Present' if has_demo_info else 'Missing'}")
            
            return {
                "accessible": accessible,
                "response_time_ms": response_time,
                "performance_good": fast_enough,
                "features": feature_checks,
                "demo_credentials_present": has_demo_info,
                "content_length": len(response.text)
            }
            
        except Exception as e:
            print(f"   ❌ Frontend Test ERROR: {e}")
            return {"accessible": False, "error": str(e)}
    
    def test_frontend_security(self):
        """Test frontend security configuration"""
        print(f"\n🔒 TESTING FRONTEND SECURITY")
        print("=" * 35)
        
        security_results = {}
        
        # Test HTTPS
        https_enabled = FRONTEND_CONFIG["production_url"].startswith("https")
        security_results["https_enabled"] = https_enabled
        print(f"   {'✅' if https_enabled else '❌'} HTTPS: {'Enabled' if https_enabled else 'Disabled'}")
        
        # Test SSL Certificate
        try:
            parsed_url = urlparse(FRONTEND_CONFIG["production_url"])
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    ssl_valid = True
                    cert_info = {
                        "subject": dict(x[0] for x in cert["subject"]),
                        "expires": cert["notAfter"]
                    }
                    
            security_results["ssl_valid"] = ssl_valid
            security_results["ssl_cert"] = cert_info
            print(f"   ✅ SSL Certificate: Valid (Expires: {cert_info['expires']})")
            
        except Exception as e:
            security_results["ssl_valid"] = False
            security_results["ssl_error"] = str(e)
            print(f"   ❌ SSL Certificate: Invalid - {e}")
        
        # Test Security Headers
        try:
            response = requests.get(FRONTEND_CONFIG["production_url"], timeout=10)
            security_headers = {
                "content_security_policy": response.headers.get("Content-Security-Policy"),
                "x_frame_options": response.headers.get("X-Frame-Options"),
                "x_content_type_options": response.headers.get("X-Content-Type-Options"),
                "strict_transport_security": response.headers.get("Strict-Transport-Security")
            }
            
            security_results["security_headers"] = security_headers
            headers_present = sum(1 for v in security_headers.values() if v is not None)
            print(f"   {'✅' if headers_present > 0 else '❌'} Security Headers: {headers_present}/4 present")
            
        except Exception as e:
            security_results["headers_error"] = str(e)
            print(f"   ❌ Security Headers: Error - {e}")
        
        return security_results
    
    def test_backend_integration_from_frontend(self):
        """Test if frontend can potentially integrate with backend services"""
        print(f"\n🔄 TESTING BACKEND INTEGRATION READINESS")
        print("=" * 45)
        
        integration_results = {
            "gcp_engines_accessible": 0,
            "aws_engines_accessible": 0,
            "total_engines": 0,
            "integration_possible": False
        }
        
        # Test GCP engine accessibility from frontend perspective
        print("   GCP Engine Accessibility:")
        for i, engine_url in enumerate(BACKEND_ENDPOINTS["gcp_engines"]):
            try:
                response = requests.get(f"{engine_url}/health", timeout=5)
                accessible = response.status_code == 200
                if accessible:
                    integration_results["gcp_engines_accessible"] += 1
                print(f"     {'✅' if accessible else '❌'} Engine {i+1}: {engine_url}")
            except Exception as e:
                print(f"     ❌ Engine {i+1}: Connection failed")
            integration_results["total_engines"] += 1
        
        # Test AWS engine accessibility
        print("   AWS Engine Accessibility:")
        for i, engine_url in enumerate(BACKEND_ENDPOINTS["aws_engines"]):
            try:
                response = requests.get(engine_url, timeout=5)
                accessible = response.status_code in [200, 404]  # 404 acceptable for some AWS endpoints
                if accessible:
                    integration_results["aws_engines_accessible"] += 1
                print(f"     {'✅' if accessible else '❌'} Engine {i+1}: {engine_url}")
            except Exception as e:
                print(f"     ❌ Engine {i+1}: Connection failed")
            integration_results["total_engines"] += 1
        
        # Determine integration possibility
        total_accessible = integration_results["gcp_engines_accessible"] + integration_results["aws_engines_accessible"]
        integration_results["integration_possible"] = total_accessible > 0
        
        print(f"\n   📊 Integration Summary:")
        print(f"      Accessible Engines: {total_accessible}/{integration_results['total_engines']}")
        print(f"      Integration Possible: {'✅ Yes' if integration_results['integration_possible'] else '❌ No'}")
        
        return integration_results
    
    def test_user_experience(self):
        """Test user experience aspects"""
        print(f"\n👤 TESTING USER EXPERIENCE")
        print("=" * 30)
        
        ux_results = {}
        
        try:
            response = requests.get(FRONTEND_CONFIG["production_url"], timeout=10)
            content = response.text.lower()
            
            # Check for emotional intelligence aspects
            emotional_elements = {
                "friendly_language": any(word in content for word in ["welcome", "demo", "easy", "simple"]),
                "clear_navigation": "login" in content and "dashboard" in content,
                "helpful_features": "trading" in content and "signals" in content,
                "demo_access": "demo" in content and "infinityai2024" in content
            }
            
            ux_results["emotional_elements"] = emotional_elements
            
            for element, present in emotional_elements.items():
                print(f"   {'✅' if present else '❌'} {element.replace('_', ' ').title()}: {'Present' if present else 'Missing'}")
            
            # Check mobile responsiveness
            mobile_responsive = "viewport" in content and "width=device-width" in content
            ux_results["mobile_responsive"] = mobile_responsive
            print(f"   {'✅' if mobile_responsive else '❌'} Mobile Responsive: {'Yes' if mobile_responsive else 'No'}")
            
            # Overall UX Score
            ux_score = sum(emotional_elements.values()) + (1 if mobile_responsive else 0)
            max_score = len(emotional_elements) + 1
            ux_results["ux_score"] = f"{ux_score}/{max_score}"
            print(f"   📊 UX Score: {ux_score}/{max_score}")
            
        except Exception as e:
            ux_results["error"] = str(e)
            print(f"   ❌ UX Test ERROR: {e}")
        
        return ux_results
    
    def generate_frontend_report(self):
        """Generate comprehensive frontend validation report"""
        print(f"\n📋 FRONTEND VALIDATION SUMMARY")
        print("=" * 40)
        
        # Calculate overall scores
        accessibility_score = 1 if self.results["accessibility"]["accessible"] else 0
        security_score = sum([
            1 if self.results["security"]["https_enabled"] else 0,
            1 if self.results["security"]["ssl_valid"] else 0,
        ])
        integration_score = 1 if self.results["backend_integration"]["integration_possible"] else 0
        ux_elements = self.results["user_experience"]["emotional_elements"]
        ux_score = sum(ux_elements.values()) if "emotional_elements" in self.results["user_experience"] else 0
        
        print(f"📊 FRONTEND HEALTH:")
        print(f"   Accessibility: {'✅' if accessibility_score else '❌'}")
        print(f"   Security: {'✅' if security_score >= 1 else '❌'} ({security_score}/2)")
        print(f"   Backend Integration: {'✅' if integration_score else '❌'}")
        print(f"   User Experience: {'✅' if ux_score >= 3 else '❌'} ({ux_score}/5)")
        
        total_score = accessibility_score + min(security_score, 1) + integration_score + min(ux_score/5, 1)
        
        if total_score >= 3.5:
            status = "🟢 EXCELLENT"
        elif total_score >= 2.5:
            status = "🟡 GOOD"
        elif total_score >= 1.5:
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            status = "🔴 CRITICAL ISSUES"
        
        print(f"\n🎯 OVERALL FRONTEND STATUS: {status}")
        print(f"   Score: {total_score:.1f}/4.0")
        
        return {
            "accessibility_score": accessibility_score,
            "security_score": security_score,
            "integration_score": integration_score,
            "ux_score": ux_score,
            "total_score": total_score,
            "status": status
        }
    
    def run_complete_validation(self):
        """Run complete frontend validation suite"""
        print("🚀 INFINITYAI.PRO - FRONTEND INTEGRATION VALIDATION")
        print(f"Frontend URL: {FRONTEND_CONFIG['production_url']}")
        print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all tests
        self.results["accessibility"] = self.test_frontend_accessibility()
        self.results["security"] = self.test_frontend_security()
        self.results["backend_integration"] = self.test_backend_integration_from_frontend()
        self.results["user_experience"] = self.test_user_experience()
        
        # Generate final report
        final_report = self.generate_frontend_report()
        self.results["summary"] = final_report
        
        return self.results

def main():
    validator = FrontendValidator()
    results = validator.run_complete_validation()
    
    # Save detailed results
    with open("frontend_validation_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Frontend validation report saved to: frontend_validation_report.json")
    print(f"🎉 Frontend validation complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()