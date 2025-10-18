#!/usr/bin/env python3
"""
InfinityAI.Pro - GCP Deployment Verification
Comprehensive health check for all Cloud Run services
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List

# ✅ CORRECTED Production URLs - Updated 2025-10-16
PRODUCTION_URLS = {
    "frontend": "https://infinityai-frontend-bprmddefsa-uc.a.run.app",
    "custom_domain": "https://infinityai.pro",
    "engines": {
        "engine_a": "https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app",
        "engine_b": "https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app",
        "engine_c": "https://engine-c-prod-bprmddefsa-uc.a.run.app",
        "engine_d": "https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app",
        "engine_ultra": "https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app"
    }
}

class DeploymentVerifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "frontend": {},
            "engines": {},
            "custom_domain": {},
            "overall_health": {}
        }
    
    def check_frontend(self):
        """Verify frontend deployment"""
        print("\n🌐 CHECKING FRONTEND")
        print("=" * 60)
        
        try:
            start = time.time()
            response = requests.get(PRODUCTION_URLS["frontend"], timeout=10)
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                content = response.text.lower()
                checks = {
                    "react_detected": "react" in content or "root" in content,
                    "infinityai_content": "infinityai" in content or "trading" in content,
                    "has_scripts": "<script" in content
                }
                
                self.results["frontend"] = {
                    "status": "✅ HEALTHY",
                    "status_code": response.status_code,
                    "response_time_ms": round(elapsed, 2),
                    "content_checks": checks,
                    "url": PRODUCTION_URLS["frontend"]
                }
                
                print(f"✅ Frontend: {response.status_code}")
                print(f"   Response Time: {elapsed:.0f}ms")
                print(f"   React Detected: {'✅' if checks['react_detected'] else '❌'}")
                print(f"   Content Valid: {'✅' if checks['infinityai_content'] else '❌'}")
            else:
                print(f"❌ Frontend: {response.status_code}")
                self.results["frontend"] = {
                    "status": "❌ FAILED",
                    "status_code": response.status_code,
                    "url": PRODUCTION_URLS["frontend"]
                }
                
        except Exception as e:
            print(f"❌ Frontend: {str(e)}")
            self.results["frontend"] = {
                "status": "❌ ERROR",
                "error": str(e),
                "url": PRODUCTION_URLS["frontend"]
            }
    
    def check_engines(self):
        """Verify all backend engines"""
        print("\n🔧 CHECKING BACKEND ENGINES")
        print("=" * 60)
        
        for engine_name, url in PRODUCTION_URLS["engines"].items():
            try:
                start = time.time()
                response = requests.get(f"{url}/health", timeout=5)
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                    except:
                        health_data = {"status": "ok"}
                    
                    self.results["engines"][engine_name] = {
                        "status": "✅ HEALTHY",
                        "status_code": response.status_code,
                        "response_time_ms": round(elapsed, 2),
                        "health_data": health_data,
                        "url": url
                    }
                    
                    print(f"✅ {engine_name.upper().replace('_', ' ')}: {response.status_code} ({elapsed:.0f}ms)")
                else:
                    print(f"⚠️  {engine_name.upper().replace('_', ' ')}: {response.status_code}")
                    self.results["engines"][engine_name] = {
                        "status": "⚠️  DEGRADED",
                        "status_code": response.status_code,
                        "url": url
                    }
                    
            except Exception as e:
                print(f"❌ {engine_name.upper().replace('_', ' ')}: Connection failed - {str(e)}")
                self.results["engines"][engine_name] = {
                    "status": "❌ FAILED",
                    "error": str(e),
                    "url": url
                }
    
    def check_custom_domain(self):
        """Check custom domain status"""
        print("\n🌍 CHECKING CUSTOM DOMAIN")
        print("=" * 60)
        
        try:
            response = requests.get(PRODUCTION_URLS["custom_domain"], timeout=10, verify=True)
            
            if response.status_code == 200:
                print(f"✅ infinityai.pro: Accessible (SSL Enabled)")
                self.results["custom_domain"] = {
                    "status": "✅ ACTIVE",
                    "status_code": response.status_code,
                    "ssl": "✅ Enabled"
                }
            else:
                print(f"⚠️  infinityai.pro: {response.status_code}")
                self.results["custom_domain"] = {
                    "status": "⚠️  DEGRADED",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.SSLError:
            print("⏳ infinityai.pro: SSL certificate pending")
            self.results["custom_domain"] = {
                "status": "⏳ PENDING",
                "note": "SSL certificate generation in progress"
            }
        except requests.exceptions.ConnectionError:
            print("⏳ infinityai.pro: DNS propagation in progress")
            self.results["custom_domain"] = {
                "status": "⏳ DNS PROPAGATING",
                "note": "Domain nameservers updated, waiting for propagation (24-48h)"
            }
        except Exception as e:
            print(f"⏳ infinityai.pro: {str(e)}")
            self.results["custom_domain"] = {
                "status": "⏳ PENDING",
                "note": str(e)
            }
    
    def calculate_overall_health(self):
        """Calculate overall system health"""
        print("\n📊 OVERALL SYSTEM HEALTH")
        print("=" * 60)
        
        # Count healthy services
        frontend_healthy = self.results["frontend"].get("status") == "✅ HEALTHY"
        
        engines_healthy = sum(
            1 for result in self.results["engines"].values() 
            if result.get("status") == "✅ HEALTHY"
        )
        total_engines = len(self.results["engines"])
        
        domain_active = self.results["custom_domain"].get("status") == "✅ ACTIVE"
        
        # Calculate scores
        frontend_score = 100 if frontend_healthy else 0
        engines_score = (engines_healthy / total_engines) * 100 if total_engines > 0 else 0
        domain_score = 100 if domain_active else 0
        
        overall_score = (frontend_score * 0.3 + engines_score * 0.6 + domain_score * 0.1)
        
        self.results["overall_health"] = {
            "score": round(overall_score, 2),
            "frontend_healthy": frontend_healthy,
            "engines_healthy": f"{engines_healthy}/{total_engines}",
            "custom_domain_active": domain_active,
            "status": self._get_health_status(overall_score)
        }
        
        print(f"\nOverall Health Score: {overall_score:.1f}%")
        print(f"Frontend: {'✅ Healthy' if frontend_healthy else '❌ Unhealthy'}")
        print(f"Engines: {engines_healthy}/{total_engines} Healthy")
        print(f"Custom Domain: {'✅ Active' if domain_active else '⏳ Pending'}")
        print(f"\nStatus: {self._get_health_status(overall_score)}")
    
    def _get_health_status(self, score):
        """Get health status based on score"""
        if score >= 90:
            return "🟢 EXCELLENT"
        elif score >= 75:
            return "🟡 GOOD"
        elif score >= 60:
            return "🟠 DEGRADED"
        else:
            return "🔴 CRITICAL"
    
    def save_results(self):
        """Save verification results to file"""
        filename = f"gcp_deployment_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
        return filename
    
    def run_verification(self):
        """Run complete verification"""
        print("\n" + "=" * 80)
        print("🚀 INFINITYAI.PRO - GCP DEPLOYMENT VERIFICATION")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.check_frontend()
        self.check_engines()
        self.check_custom_domain()
        self.calculate_overall_health()
        filename = self.save_results()
        
        print("\n" + "=" * 80)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 80)
        print(f"\n📄 Full report: {filename}")
        
        return self.results

if __name__ == "__main__":
    verifier = DeploymentVerifier()
    results = verifier.run_verification()
    
    # Print next steps
    print("\n📋 NEXT STEPS:")
    print("=" * 60)
    
    if results["overall_health"]["score"] >= 75:
        print("✅ System is healthy! You can proceed with:")
        print("   1. Testing the application at the Cloud Run URL")
        print("   2. Configuring custom domain DNS (if not done)")
        print("   3. Setting up monitoring and alerts")
    else:
        print("⚠️  System needs attention:")
        unhealthy = [
            engine for engine, data in results["engines"].items()
            if data.get("status") != "✅ HEALTHY"
        ]
        if unhealthy:
            print(f"   - Fix unhealthy engines: {', '.join(unhealthy)}")
        if not results["overall_health"]["frontend_healthy"]:
            print("   - Fix frontend deployment")
    
    print("\n🌐 Custom Domain Setup:")
    if results["custom_domain"].get("status") != "✅ ACTIVE":
        print("   1. Go to Namecheap dashboard")
        print("   2. Select infinityai.pro domain")
        print("   3. Set nameservers to GCP Cloud DNS nameservers")
        print("   4. Wait 24-48 hours for DNS propagation")
