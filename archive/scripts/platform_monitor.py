#!/usr/bin/env python3
"""
InfinityAI.Pro - Continuous Platform Health Monitor
===================================================
Monitors all engines, Firebase Functions, and dashboard health.
"""

import requests
import json
import time
from datetime import datetime

class PlatformMonitor:
    def __init__(self):
        self.engines = {
            "engine-a": "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app",
            "engine-b": "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app", 
            "engine-c": "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app",
            "engine-d": "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app"
        }
        self.functions_base = "https://us-central1-infinity-ai-5ec7c.cloudfunctions.net"
        self.frontend_url = "https://infinity-ai-5ec7c.web.app"
        
    def check_engine_health(self):
        """Check all engines health"""
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Checking Engine Health")
        
        for name, url in self.engines.items():
            try:
                response = requests.get(f"{url}/health", timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ {name}: Healthy")
                else:
                    print(f"  ❌ {name}: Error ({response.status_code})")
            except Exception as e:
                print(f"  ❌ {name}: Connection failed")
    
    def check_functions_health(self):
        """Check Firebase Functions"""
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Checking Functions")
        
        functions = ["submitDhanCredentialsV2", "analyzePortfolio", "getGeminiAnalysis"]
        
        for func in functions:
            try:
                response = requests.post(f"{self.functions_base}/{func}", 
                                       json={"data": {"test": True}}, timeout=10)
                if response.status_code in [200, 401, 403]:
                    print(f"  ✅ {func}: Available")
                else:
                    print(f"  ❌ {func}: Error ({response.status_code})")
            except Exception as e:
                print(f"  ❌ {func}: Failed")
    
    def check_frontend_health(self):
        """Check frontend accessibility"""
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Checking Frontend")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Frontend: Accessible")
            else:
                print(f"  ❌ Frontend: Error ({response.status_code})")
        except Exception as e:
            print(f"  ❌ Frontend: Failed")
    
    def run_continuous_monitoring(self, interval=60):
        """Run continuous monitoring"""
        print("🔍 Starting Continuous Platform Monitoring")
        print("=" * 60)
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.check_engine_health()
                self.check_functions_health()  
                self.check_frontend_health()
                
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    monitor = PlatformMonitor()
    monitor.run_continuous_monitoring()
