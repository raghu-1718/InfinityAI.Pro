#!/usr/bin/env python3
"""
InfinityAI.Pro - AWS ALB Engine C Routing Fix
Diagnosis and fix recommendations for Engine C routing issues
"""

import requests
import json
import time
from datetime import datetime

# AWS Configuration
ALB_ENDPOINT = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com"
ENGINE_C_PATH = "/engine-c"
ENGINE_D_PATH = "/engine-d"

class AWSRoutingDiagnostic:
    def __init__(self):
        self.results = {}
        
    def test_alb_base(self):
        """Test base ALB response"""
        print("🔍 DIAGNOSING AWS APPLICATION LOAD BALANCER")
        print("=" * 50)
        
        try:
            response = requests.get(ALB_ENDPOINT, timeout=10)
            print(f"   ALB Base URL: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            print(f"   Content: {response.text[:200]}")
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:200]
            }
        except Exception as e:
            print(f"   ❌ ALB Base Test ERROR: {e}")
            return {"error": str(e)}
    
    def test_engine_paths(self):
        """Test specific engine paths"""
        print(f"\n🔍 TESTING ENGINE PATHS")
        print("=" * 30)
        
        paths_to_test = [
            ENGINE_C_PATH,
            ENGINE_D_PATH,
            "/",
            "/health",
            "/api/health"
        ]
        
        results = {}
        
        for path in paths_to_test:
            try:
                url = f"{ALB_ENDPOINT}{path}"
                response = requests.get(url, timeout=10)
                
                results[path] = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "server": response.headers.get("server", ""),
                    "content_preview": response.text[:100]
                }
                
                status = "✅" if response.status_code == 200 else "❌" if response.status_code == 404 else "⚠️"
                print(f"   {status} {path}: {response.status_code} - {response.text[:50]}")
                
            except Exception as e:
                results[path] = {"error": str(e)}
                print(f"   ❌ {path}: ERROR - {e}")
        
        return results
    
    def analyze_routing_issue(self):
        """Analyze the root cause of routing issues"""
        print(f"\n🔍 ANALYZING ROUTING CONFIGURATION")
        print("=" * 40)
        
        # Check if ALB is returning 404 for engine paths
        engine_c_response = requests.get(f"{ALB_ENDPOINT}{ENGINE_C_PATH}", timeout=10)
        engine_d_response = requests.get(f"{ALB_ENDPOINT}{ENGINE_D_PATH}", timeout=10)
        
        diagnosis = {
            "engine_c_reachable": engine_c_response.status_code == 200,
            "engine_d_reachable": engine_d_response.status_code == 200,
            "alb_responding": True,  # If we get here, ALB is responding
            "routing_configured": False
        }
        
        # Analyze response patterns
        if engine_c_response.status_code == 404 and "Not Found" in engine_c_response.text:
            diagnosis["issue_type"] = "ALB Listener Rules Missing"
            diagnosis["root_cause"] = "Path-based routing rules not configured on ALB listener"
        elif engine_c_response.status_code == 503:
            diagnosis["issue_type"] = "Target Group Unhealthy"
            diagnosis["root_cause"] = "ECS tasks are not healthy or not registered with target group"
        else:
            diagnosis["issue_type"] = "Unknown"
            diagnosis["root_cause"] = f"Unexpected response: {engine_c_response.status_code}"
        
        print(f"   Issue Type: {diagnosis['issue_type']}")
        print(f"   Root Cause: {diagnosis['root_cause']}")
        print(f"   Engine C Status: {engine_c_response.status_code}")
        print(f"   Engine D Status: {engine_d_response.status_code}")
        
        return diagnosis
    
    def generate_fix_recommendations(self, diagnosis):
        """Generate specific fix recommendations"""
        print(f"\n🔧 GENERATING FIX RECOMMENDATIONS")
        print("=" * 40)
        
        recommendations = []
        
        if diagnosis["issue_type"] == "ALB Listener Rules Missing":
            recommendations = [
                {
                    "priority": "HIGH",
                    "action": "Configure ALB Listener Rules",
                    "steps": [
                        "1. Access AWS Console → EC2 → Load Balancers",
                        "2. Select infinityai-alb-124143296",
                        "3. Go to Listeners tab → Select HTTP:80 listener",
                        "4. Add Rule: IF Path = /engine-c* THEN Forward to infinityai-tg-engine-c",
                        "5. Add Rule: IF Path = /engine-d* THEN Forward to infinityai-tg-engine-d",
                        "6. Set rule priorities appropriately (lower number = higher priority)"
                    ],
                    "aws_cli_commands": [
                        "aws elbv2 create-rule --listener-arn <LISTENER_ARN> --priority 100 --conditions Field=path-pattern,Values='/engine-c*' --actions Type=forward,TargetGroupArn=<ENGINE_C_TARGET_GROUP_ARN>",
                        "aws elbv2 create-rule --listener-arn <LISTENER_ARN> --priority 101 --conditions Field=path-pattern,Values='/engine-d*' --actions Type=forward,TargetGroupArn=<ENGINE_D_TARGET_GROUP_ARN>"
                    ]
                },
                {
                    "priority": "MEDIUM",
                    "action": "Verify Target Group Health",
                    "steps": [
                        "1. Check that ECS tasks are running and healthy",
                        "2. Verify target group health checks are passing",
                        "3. Ensure security group rules allow ALB to ECS communication"
                    ]
                }
            ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n   🔧 RECOMMENDATION {i} - {rec['priority']} PRIORITY")
            print(f"      Action: {rec['action']}")
            print(f"      Steps:")
            for step in rec['steps']:
                print(f"         {step}")
            
            if 'aws_cli_commands' in rec:
                print(f"      AWS CLI Commands:")
                for cmd in rec['aws_cli_commands']:
                    print(f"         {cmd}")
        
        return recommendations
    
    def test_fix_verification(self):
        """Test to verify if routing fix works"""
        print(f"\n✅ VERIFICATION TEST (Run after applying fixes)")
        print("=" * 50)
        
        test_urls = [
            f"{ALB_ENDPOINT}{ENGINE_C_PATH}",
            f"{ALB_ENDPOINT}{ENGINE_C_PATH}/health",
            f"{ALB_ENDPOINT}{ENGINE_D_PATH}",
            f"{ALB_ENDPOINT}{ENGINE_D_PATH}/health"
        ]
        
        print("   Expected Results After Fix:")
        for url in test_urls:
            print(f"      {url} → Should return 200 OK")
        
        print(f"\n   Current Results:")
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                status = "✅" if response.status_code == 200 else "❌"
                print(f"      {status} {url} → {response.status_code}")
            except Exception as e:
                print(f"      ❌ {url} → ERROR: {e}")
    
    def run_complete_diagnosis(self):
        """Run complete AWS routing diagnosis"""
        print("🚀 AWS ENGINE C ROUTING DIAGNOSIS")
        print(f"ALB Endpoint: {ALB_ENDPOINT}")
        print(f"Diagnosis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run diagnostic tests
        alb_base = self.test_alb_base()
        path_tests = self.test_engine_paths()
        diagnosis = self.analyze_routing_issue()
        recommendations = self.generate_fix_recommendations(diagnosis)
        self.test_fix_verification()
        
        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "alb_base_test": alb_base,
            "path_tests": path_tests,
            "diagnosis": diagnosis,
            "recommendations": recommendations
        }
        
        # Save detailed results
        with open("aws_routing_diagnosis.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed diagnosis saved to: aws_routing_diagnosis.json")
        
        return results

def main():
    diagnostic = AWSRoutingDiagnostic()
    results = diagnostic.run_complete_diagnosis()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Issue: {results['diagnosis']['issue_type']}")
    print(f"   Engine C Status: {results['path_tests'][ENGINE_C_PATH]['status_code']}")
    print(f"   Fix Required: Configure ALB listener rules for path-based routing")
    print(f"   Estimated Fix Time: 5-10 minutes via AWS Console")

if __name__ == "__main__":
    main()