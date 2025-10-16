#!/usr/bin/env python3
"""
InfinityAI.Pro - Continuous Monitoring & Auto-Recovery
Real-time monitoring with automatic issue detection and recovery
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import subprocess
import os

class ContinuousMonitor:
    def __init__(self):
        self.project_id = "after-yesterday-473512-k3"
        self.region = "us-central1"
        
        self.services = {
            "engine-a-market-data": "https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app",
            "engine-b-ai-ml": "https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app",
            "engine-c": "https://engine-c-prod-bprmddefsa-uc.a.run.app",  # Corrected service name
            "engine-d-chatbot": "https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app",
            "engine-ultra-aggressive": "https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app",
            "frontend": "https://infinityai-frontend-bprmddefsa-uc.a.run.app"
        }
        
        self.health_history = {name: [] for name in self.services.keys()}
        self.alert_sent = {name: False for name in self.services.keys()}
        
        # Thresholds
        self.latency_threshold = 5000  # ms
        self.failure_threshold = 3  # consecutive failures
        
    def check_service_health(self, name: str, url: str) -> Dict:
        """Check health of a single service"""
        try:
            start = time.time()
            response = requests.get(f"{url}/health", timeout=15)
            latency = round((time.time() - start) * 1000, 2)
            
            status = {
                "service": name,
                "url": url,
                "status_code": response.status_code,
                "latency_ms": latency,
                "healthy": response.status_code == 200,
                "slow": latency > self.latency_threshold,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "response": response.text[:100] if response.text else None
            }
            
            return status
            
        except requests.exceptions.Timeout:
            return {
                "service": name,
                "url": url,
                "status_code": "TIMEOUT",
                "healthy": False,
                "error": "Request timed out",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            return {
                "service": name,
                "url": url,
                "status_code": "ERROR",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def check_all_services(self) -> List[Dict]:
        """Check all services"""
        results = []
        
        for name, url in self.services.items():
            result = self.check_service_health(name, url)
            results.append(result)
            
            # Update history
            self.health_history[name].append(result)
            # Keep only last 10 checks
            if len(self.health_history[name]) > 10:
                self.health_history[name] = self.health_history[name][-10:]
        
        return results
    
    def detect_issues(self, results: List[Dict]) -> List[Dict]:
        """Detect issues that need attention"""
        issues = []
        
        for result in results:
            name = result["service"]
            
            # Check for unhealthy service
            if not result.get("healthy"):
                consecutive_failures = sum(
                    1 for check in self.health_history[name][-self.failure_threshold:]
                    if not check.get("healthy")
                )
                
                if consecutive_failures >= self.failure_threshold:
                    issues.append({
                        "service": name,
                        "severity": "critical",
                        "issue": "Service is down",
                        "consecutive_failures": consecutive_failures,
                        "action": "restart_service"
                    })
            
            # Check for high latency
            if result.get("slow"):
                issues.append({
                    "service": name,
                    "severity": "warning",
                    "issue": f"High latency ({result['latency_ms']}ms)",
                    "action": "investigate_performance"
                })
        
        return issues
    
    def auto_recover(self, issue: Dict) -> Dict:
        """Attempt automatic recovery"""
        service_name = issue["service"]
        action = issue.get("action")
        
        recovery_result = {
            "service": service_name,
            "action": action,
            "attempted": True,
            "success": False,
            "message": ""
        }
        
        if action == "restart_service":
            # In production, this would trigger a Cloud Run revision rollout
            print(f"🔄 Attempting auto-recovery for {service_name}...")
            
            # For now, just log the action
            recovery_result["success"] = True
            recovery_result["message"] = f"Would restart {service_name} (dry-run mode)"
            
        elif action == "investigate_performance":
            recovery_result["success"] = True
            recovery_result["message"] = f"Performance alert logged for {service_name}"
        
        return recovery_result
    
    def generate_status_report(self, results: List[Dict], issues: List[Dict]) -> str:
        """Generate status report"""
        report = []
        report.append("=" * 70)
        report.append("🔍 InfinityAI.Pro - Live Monitoring Dashboard")
        report.append("=" * 70)
        report.append(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report.append("")
        
        # Service Status
        report.append("📊 Service Status:")
        report.append("-" * 70)
        
        healthy_count = sum(1 for r in results if r.get("healthy"))
        total_count = len(results)
        
        for result in results:
            status_icon = "✅" if result.get("healthy") else "❌"
            latency = result.get("latency_ms", "N/A")
            status = result.get("status_code", "ERROR")
            
            report.append(
                f"{status_icon} {result['service']:25} | "
                f"Status: {status:8} | "
                f"Latency: {latency:8}ms"
            )
        
        report.append("")
        report.append(f"Overall Health: {healthy_count}/{total_count} services operational")
        
        # Issues
        if issues:
            report.append("")
            report.append("🚨 Active Issues:")
            report.append("-" * 70)
            
            for issue in issues:
                severity_icon = "🔴" if issue["severity"] == "critical" else "🟡"
                report.append(
                    f"{severity_icon} {issue['service']:25} | "
                    f"{issue['issue']}"
                )
        else:
            report.append("")
            report.append("✅ No issues detected")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def run_monitoring_cycle(self, iterations: int = 1, interval: int = 60):
        """Run monitoring for specified iterations"""
        print(f"🚀 Starting continuous monitoring ({iterations} cycle(s), {interval}s interval)")
        print("")
        
        for i in range(iterations):
            print(f"Cycle {i + 1}/{iterations}")
            
            # Check all services
            results = self.check_all_services()
            
            # Detect issues
            issues = self.detect_issues(results)
            
            # Generate report
            report = self.generate_status_report(results, issues)
            print(report)
            
            # Auto-recovery if needed
            if issues:
                print("\n🔧 Attempting auto-recovery...")
                for issue in issues:
                    if issue["severity"] == "critical":
                        recovery = self.auto_recover(issue)
                        if recovery["success"]:
                            print(f"✅ {recovery['message']}")
                        else:
                            print(f"❌ Recovery failed: {recovery['message']}")
            
            # Save results
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"/workspaces/InfinityAI.Pro/logs/monitoring_{timestamp}.json"
            
            os.makedirs("/workspaces/InfinityAI.Pro/logs", exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "cycle": i + 1,
                    "results": results,
                    "issues": issues,
                    "health_rate": f"{sum(1 for r in results if r.get('healthy'))}/{len(results)}"
                }, f, indent=2)
            
            print(f"\n📝 Results saved to {results_file}")
            
            # Wait for next cycle
            if i < iterations - 1:
                print(f"\n⏸️  Waiting {interval}s for next cycle...\n")
                time.sleep(interval)
        
        print("\n✅ Monitoring complete")


def main():
    monitor = ContinuousMonitor()
    
    # Single monitoring cycle
    monitor.run_monitoring_cycle(iterations=1, interval=60)


if __name__ == "__main__":
    main()
