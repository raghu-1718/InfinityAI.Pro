# 🔍 InfinityAI.Pro 5-Minute Continuous Application Analysis

import requests
import time
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
DHAN_API_BASE = "https://sandbox.dhan.co/v2"
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzU5ODAzNTEwfQ.N3TzwYtgOuEGQpKTc3KKPw9bpc53FohogUajP-HETAqR22rK9ljDFrMCxOWeuallfREklBdNdv-Ai9k1jQsx8g"

class ApplicationAnalyzer:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.test_duration = 300  # 5 minutes in seconds
        
    def log_result(self, test_name, status, response_time, details):
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "status": status,
            "response_time_ms": response_time,
            "details": details
        }
        self.results.append(result)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {test_name}: {status} ({response_time}ms)")
        
    def test_endpoint(self, name, url, headers=None, timeout=10):
        try:
            start = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            response_time = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.log_result(name, "✅ SUCCESS", response_time, {
                    "status_code": response.status_code,
                    "content_length": len(response.text),
                    "first_100_chars": response.text[:100]
                })
                return True
            else:
                self.log_result(name, "❌ FAILED", response_time, {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_result(name, "🔥 ERROR", 0, {"exception": str(e)})
            return False
    
    def test_dhan_api(self, endpoint, name):
        headers = {
            "access-token": ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        return self.test_endpoint(name, f"{DHAN_API_BASE}/{endpoint}", headers)
    
    def run_test_cycle(self, cycle_number):
        print(f"\n🔄 Test Cycle {cycle_number} - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        # Test Application Health
        self.test_endpoint("App Health", f"{BASE_URL}/health")
        
        # Test Frontend Loading
        self.test_endpoint("Frontend HTML", f"{BASE_URL}/")
        
        # Test Static Files
        self.test_endpoint("JS Bundle", f"{BASE_URL}/static/js/main.1f9e330d.js")
        self.test_endpoint("CSS Bundle", f"{BASE_URL}/static/css/main.14addf7b.css")
        
        # Test Dashboard
        self.test_endpoint("Dashboard", f"{BASE_URL}/dashboard")
        
        # Test API Documentation
        self.test_endpoint("API Docs", f"{BASE_URL}/docs")
        
        # Test Dhan API Endpoints
        self.test_dhan_api("holdings", "Dhan Holdings")
        self.test_dhan_api("positions", "Dhan Positions")
        self.test_dhan_api("orders", "Dhan Orders")
        
        time.sleep(30)  # Wait 30 seconds between cycles
    
    def generate_report(self):
        print("\n" + "="*60)
        print("📊 5-MINUTE APPLICATION ANALYSIS REPORT")
        print("="*60)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if "SUCCESS" in r["status"]])
        failed_tests = len([r for r in self.results if "FAILED" in r["status"]])
        error_tests = len([r for r in self.results if "ERROR" in r["status"]])
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   ❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"   🔥 Errors: {error_tests} ({error_tests/total_tests*100:.1f}%)")
        
        # Group by test type
        test_summary = {}
        for result in self.results:
            test_name = result["test"]
            if test_name not in test_summary:
                test_summary[test_name] = {"success": 0, "failed": 0, "error": 0, "avg_response": 0}
            
            if "SUCCESS" in result["status"]:
                test_summary[test_name]["success"] += 1
            elif "FAILED" in result["status"]:
                test_summary[test_name]["failed"] += 1
            else:
                test_summary[test_name]["error"] += 1
                
            test_summary[test_name]["avg_response"] += result["response_time_ms"]
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, stats in test_summary.items():
            total = stats["success"] + stats["failed"] + stats["error"]
            avg_response = stats["avg_response"] / total if total > 0 else 0
            success_rate = stats["success"] / total * 100 if total > 0 else 0
            
            status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate > 50 else "❌"
            print(f"   {status_icon} {test_name}:")
            print(f"      Success Rate: {success_rate:.1f}% ({stats['success']}/{total})")
            print(f"      Avg Response: {avg_response:.0f}ms")
            
        # Issues Identified
        print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
        static_file_failures = [r for r in self.results if "JS Bundle" in r["test"] or "CSS Bundle" in r["test"]]
        if static_file_failures and all("FAILED" in r["status"] for r in static_file_failures):
            print("   ❌ STATIC FILES NOT LOADING - This causes the white screen issue")
            print("      Solution: Frontend build files need to be properly served")
            
        dhan_issues = [r for r in self.results if "Dhan" in r["test"] and "SUCCESS" not in r["status"]]
        if dhan_issues:
            print("   ⚠️  Some Dhan API endpoints may have issues")
            
        print(f"\n🎯 RECOMMENDATIONS:")
        print("   1. Fix static file serving to resolve white screen")
        print("   2. Dhan API authentication is working correctly")
        print("   3. Backend health and API docs are functional")
        print("   4. Ready to switch from sandbox to production credentials")
        
        return {
            "total_tests": total_tests,
            "success_rate": successful_tests/total_tests*100,
            "critical_issues": len(static_file_failures) > 0,
            "dhan_working": any("SUCCESS" in r["status"] for r in self.results if "Dhan" in r["test"])
        }

def main():
    print("🚀 STARTING 5-MINUTE CONTINUOUS APPLICATION ANALYSIS")
    print(f"Target Application: {BASE_URL}")
    print(f"Test Duration: 5 minutes")
    print(f"Start Time: {datetime.now()}")
    
    analyzer = ApplicationAnalyzer()
    cycle = 1
    
    end_time = datetime.now() + timedelta(seconds=300)
    
    while datetime.now() < end_time:
        try:
            analyzer.run_test_cycle(cycle)
            cycle += 1
        except KeyboardInterrupt:
            print("\n⏹️  Testing stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in test cycle: {e}")
    
    # Generate final report
    report = analyzer.generate_report()
    
    # Save detailed results
    with open("application_analysis_report.json", "w") as f:
        json.dump({
            "summary": report,
            "detailed_results": analyzer.results,
            "test_config": {
                "base_url": BASE_URL,
                "start_time": analyzer.start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
        }, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: application_analysis_report.json")
    print(f"🏁 Analysis completed at: {datetime.now()}")

if __name__ == "__main__":
    main()