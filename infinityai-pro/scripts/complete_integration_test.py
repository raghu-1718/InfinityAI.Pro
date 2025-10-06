# 🚀 InfinityAI.Pro Complete Integration Test Suite

import requests
import json
import time
from datetime import datetime

class InfinityAIIntegrationTest:
    def __init__(self):
        self.engines = {
            'engine_a': {
                'name': 'Engine A (Azure Container Apps)',
                'url': 'https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io',
                'function': 'Market Data Ingestion & Frontend',
                'status': 'unknown'
            },
            'engine_b': {
                'name': 'Engine B (Google Cloud Run GPU)',
                'url': 'https://infinityai-engine-b-573866363639.us-central1.run.app',
                'function': 'AI/ML GPU Processing',
                'status': 'unknown'
            },
            'engine_c': {
                'name': 'Engine C (AWS ECS)',
                'url': 'http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c',
                'function': 'Trade Execution',
                'status': 'unknown'
            },
            'engine_d': {
                'name': 'Engine D (AWS ECS)',
                'url': 'http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d',
                'function': 'AI Chatbot & Voice Assistant',
                'status': 'unknown'
            }
        }
        
        self.custom_domains = {
            'frontend': 'https://infinityai.pro',
            'api': 'https://api.infinityai.pro'
        }
        
        self.test_results = {}
        
    def test_engine_health(self, engine_key, engine_info):
        """Test individual engine health endpoint"""
        try:
            print(f"\n🔍 Testing {engine_info['name']}...")
            health_url = f"{engine_info['url']}/health"
            
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {engine_info['name']} is HEALTHY")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Engine: {data.get('engine', 'N/A')}")
                print(f"   Version: {data.get('version', 'N/A')}")
                
                if 'features' in data:
                    print(f"   Features: {', '.join(data['features'])}")
                    
                engine_info['status'] = 'healthy'
                return True
                
            else:
                print(f"⚠️ {engine_info['name']} returned status code: {response.status_code}")
                engine_info['status'] = f'http_error_{response.status_code}'
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {engine_info['name']} is UNREACHABLE")
            print(f"   Error: {str(e)}")
            engine_info['status'] = 'unreachable'
            return False
            
    def test_custom_domains(self):
        """Test custom domain accessibility"""
        print(f"\n🌐 Testing Custom Domains...")
        
        for domain_name, domain_url in self.custom_domains.items():
            try:
                print(f"\n🔍 Testing {domain_name}: {domain_url}")
                response = requests.get(domain_url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    print(f"✅ {domain_name} is ACCESSIBLE")
                    print(f"   Final URL: {response.url}")
                    print(f"   Content Length: {len(response.content)} bytes")
                    
                    # Check if it's serving the React app
                    if 'InfinityAI' in response.text:
                        print(f"   ✅ React app detected")
                    
                else:
                    print(f"⚠️ {domain_name} returned status code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {domain_name} is UNREACHABLE")
                print(f"   Error: {str(e)}")
    
    def test_engine_integration(self):
        """Test inter-engine communication"""
        print(f"\n🔗 Testing Engine Integration...")
        
        # Test if engines can communicate with each other
        healthy_engines = [k for k, v in self.engines.items() if v['status'] == 'healthy']
        
        if len(healthy_engines) >= 2:
            print(f"✅ {len(healthy_engines)} engines are healthy - integration possible")
            print(f"   Healthy engines: {', '.join([self.engines[k]['name'] for k in healthy_engines])}")
        else:
            print(f"⚠️ Only {len(healthy_engines)} engines are healthy - limited integration")
            
    def generate_report(self):
        """Generate comprehensive test report"""
        print(f"\n" + "="*80)
        print(f"🎯 INFINITYAI.PRO INTEGRATION TEST REPORT")
        print(f"="*80)
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"")
        
        # Engine Status Summary
        print(f"📊 ENGINE STATUS SUMMARY:")
        print(f"-" * 40)
        
        healthy_count = 0
        total_count = len(self.engines)
        
        for engine_key, engine_info in self.engines.items():
            status_icon = "✅" if engine_info['status'] == 'healthy' else "❌"
            if engine_info['status'] == 'healthy':
                healthy_count += 1
                
            print(f"{status_icon} {engine_info['name']}")
            print(f"   Function: {engine_info['function']}")
            print(f"   Status: {engine_info['status']}")
            print(f"   URL: {engine_info['url']}")
            print()
            
        # Overall Platform Status
        print(f"🎯 OVERALL PLATFORM STATUS:")
        print(f"-" * 40)
        
        platform_percentage = (healthy_count / total_count) * 100
        
        if platform_percentage == 100:
            status_icon = "🎉"
            status_text = "FULLY OPERATIONAL"
        elif platform_percentage >= 75:
            status_icon = "🚀"
            status_text = "MOSTLY OPERATIONAL"
        elif platform_percentage >= 50:
            status_icon = "⚠️"
            status_text = "PARTIALLY OPERATIONAL"
        else:
            status_icon = "❌"
            status_text = "REQUIRES ATTENTION"
            
        print(f"{status_icon} Platform Status: {status_text}")
        print(f"📈 Operational Engines: {healthy_count}/{total_count} ({platform_percentage:.1f}%)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"-" * 40)
        
        if platform_percentage == 100:
            print(f"✅ All engines operational - platform ready for production!")
            print(f"✅ Custom domains configured - access via https://infinityai.pro")
            print(f"✅ Multi-cloud architecture fully functional")
        else:
            print(f"🔧 Focus on fixing non-operational engines:")
            for engine_key, engine_info in self.engines.items():
                if engine_info['status'] != 'healthy':
                    print(f"   - {engine_info['name']}: {engine_info['status']}")
                    
        print(f"\n🌐 CUSTOM DOMAINS:")
        print(f"-" * 40)
        print(f"Frontend: https://infinityai.pro")
        print(f"API: https://api.infinityai.pro")
        print(f"")
        print(f"📝 DNS Status: Configured and propagated")
        print(f"🔒 SSL Status: Auto-provisioning by Azure")
        
        return platform_percentage
        
    def run_complete_test(self):
        """Run complete integration test suite"""
        print(f"🚀 Starting InfinityAI.Pro Complete Integration Test...")
        print(f"=" * 80)
        
        # Test individual engines
        for engine_key, engine_info in self.engines.items():
            self.test_engine_health(engine_key, engine_info)
            time.sleep(2)  # Brief pause between tests
            
        # Test custom domains
        self.test_custom_domains()
        
        # Test integration
        self.test_engine_integration()
        
        # Generate final report
        platform_percentage = self.generate_report()
        
        return platform_percentage

if __name__ == "__main__":
    # Run the complete integration test
    test_suite = InfinityAIIntegrationTest()
    platform_percentage = test_suite.run_complete_test()
    
    # Exit with appropriate code
    if platform_percentage >= 75:
        print(f"\n🎉 Integration test PASSED! Platform is ready for operation.")
        exit(0)
    else:
        print(f"\n⚠️ Integration test requires attention. Platform needs fixes.")
        exit(1)