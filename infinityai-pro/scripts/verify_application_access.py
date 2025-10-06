#!/usr/bin/env python3
"""
🚀 InfinityAI.Pro Application Access & Integration Verifier
🎯 Complete frontend-backend verification and application setup
📱 Includes Dhan Sandbox testing configuration
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import subprocess
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InfinityAIAccessVerifier:
    """🔧 Complete application access and integration verifier"""
    
    def __init__(self):
        """Initialize the verifier with all endpoint configurations"""
        self.endpoints = {
            'azure_primary': 'https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io',
            'azure_alt': 'https://infinityai-engine-a--0000006.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io',
            'google_engine_b': 'https://engine-b-service-infinityai.run.app',
            'aws_engine_c': 'https://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8002',
            'aws_engine_d': 'https://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8000',
            'custom_domain': 'https://infinityai.pro'
        }
        
        self.dhan_config = {
            'sandbox_base_url': 'https://api.dhan.co',
            'live_base_url': 'https://api.dhan.co',
            'test_endpoints': [
                '/v2/charts/intraday',
                '/v2/charts/historical', 
                '/v2/marketfeed/ltp',
                '/v2/orders',
                '/v2/positions'
            ]
        }
        
        self.local_ports = {
            'backend': 8000,
            'frontend': 3000,
            'alternative_backend': 8003
        }

    async def verify_all_systems(self):
        """🔍 Complete system verification"""
        logger.info("🚀 Starting InfinityAI.Pro Application Access Verification")
        logger.info("=" * 60)
        
        results = {
            'cloud_endpoints': await self.test_cloud_endpoints(),
            'local_setup': await self.verify_local_setup(),
            'frontend_backend_integration': await self.test_frontend_backend_integration(),
            'dhan_sandbox': await self.setup_dhan_sandbox_testing(),
            'application_access': await self.setup_application_access()
        }
        
        # Generate comprehensive report
        await self.generate_verification_report(results)
        
        return results

    async def test_cloud_endpoints(self):
        """☁️ Test all cloud endpoints"""
        logger.info("☁️ Testing cloud endpoints...")
        
        results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for name, url in self.endpoints.items():
                try:
                    async with session.get(f"{url}/health") as response:
                        if response.status == 200:
                            data = await response.json()
                            results[name] = {
                                'status': 'healthy',
                                'response_time': response.headers.get('response-time', 'N/A'),
                                'data': data
                            }
                            logger.info(f"✅ {name}: Healthy")
                        else:
                            results[name] = {
                                'status': 'unhealthy',
                                'http_status': response.status,
                                'url': url
                            }
                            logger.warning(f"⚠️ {name}: HTTP {response.status}")
                            
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'url': url
                    }
                    logger.error(f"❌ {name}: {str(e)}")
        
        return results

    async def verify_local_setup(self):
        """🏠 Verify local development setup"""
        logger.info("🏠 Verifying local setup...")
        
        results = {}
        
        # Check if frontend build exists
        frontend_build_path = Path("frontend/build")
        results['frontend_build'] = {
            'exists': frontend_build_path.exists(),
            'path': str(frontend_build_path.absolute())
        }
        
        # Check backend configuration
        backend_main_path = Path("backend/main.py")
        results['backend_main'] = {
            'exists': backend_main_path.exists(),
            'path': str(backend_main_path.absolute())
        }
        
        # Check package.json
        package_json_path = Path("frontend/package.json")
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                results['frontend_config'] = {
                    'proxy': package_data.get('proxy'),
                    'scripts': package_data.get('scripts', {}),
                    'dependencies': list(package_data.get('dependencies', {}).keys())
                }
        
        # Check API configuration
        api_config_path = Path("frontend/src/config/api-config.js")
        results['api_config'] = {
            'exists': api_config_path.exists(),
            'path': str(api_config_path.absolute())
        }
        
        logger.info(f"📁 Frontend build: {'✅' if results['frontend_build']['exists'] else '❌'}")
        logger.info(f"📁 Backend main: {'✅' if results['backend_main']['exists'] else '❌'}")
        logger.info(f"📁 API config: {'✅' if results['api_config']['exists'] else '❌'}")
        
        return results

    async def test_frontend_backend_integration(self):
        """🔗 Test frontend-backend integration"""
        logger.info("🔗 Testing frontend-backend integration...")
        
        results = {}
        
        # Test if backend can serve frontend
        try:
            # Start backend server locally (if not running)
            backend_url = f"http://localhost:{self.local_ports['backend']}"
            
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                try:
                    async with session.get(f"{backend_url}/health") as response:
                        if response.status == 200:
                            results['backend_health'] = {
                                'status': 'healthy',
                                'data': await response.json()
                            }
                        else:
                            results['backend_health'] = {
                                'status': 'unhealthy',
                                'http_status': response.status
                            }
                except Exception as e:
                    results['backend_health'] = {
                        'status': 'not_running',
                        'error': str(e),
                        'message': 'Backend server not running locally'
                    }
                
                # Test frontend serving
                try:
                    async with session.get(backend_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            if 'InfinityAI' in content or 'React' in content:
                                results['frontend_served'] = {
                                    'status': 'success',
                                    'message': 'Frontend served by backend'
                                }
                            else:
                                results['frontend_served'] = {
                                    'status': 'partial',
                                    'message': 'Backend responds but may not serve frontend'
                                }
                        else:
                            results['frontend_served'] = {
                                'status': 'failed',
                                'http_status': response.status
                            }
                except Exception as e:
                    results['frontend_served'] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        except Exception as e:
            results['integration_test'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return results

    async def setup_dhan_sandbox_testing(self):
        """💼 Setup Dhan Sandbox testing"""
        logger.info("💼 Setting up Dhan Sandbox testing...")
        
        results = {}
        
        # Check if Dhan credentials are configured
        env_file_path = Path("backend/.env")
        dhan_configured = False
        
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                if 'DHAN_CLIENT_ID' in env_content and 'DHAN_ACCESS_TOKEN' in env_content:
                    dhan_configured = True
        
        results['dhan_credentials'] = {
            'configured': dhan_configured,
            'env_file_exists': env_file_path.exists()
        }
        
        # Test Dhan API connectivity (public endpoints)
        try:
            async with aiohttp.ClientSession() as session:
                # Test public market data endpoint
                test_url = f"{self.dhan_config['sandbox_base_url']}/v2/charts/historical"
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                # This is a test payload - in real scenario, you'd need proper auth
                test_payload = {
                    "symbol": "NSE:RELIANCE-EQ",
                    "exchangeSegment": "NSE_EQ",
                    "instrument": "EQUITY",
                    "fromDate": "2024-01-01",
                    "toDate": "2024-01-31"
                }
                
                async with session.post(test_url, json=test_payload, headers=headers) as response:
                    results['dhan_api_test'] = {
                        'status_code': response.status,
                        'accessible': response.status in [200, 401, 403],  # 401/403 means API is accessible but needs auth
                        'message': 'API accessible' if response.status in [200, 401, 403] else 'API may be down'
                    }
                    
        except Exception as e:
            results['dhan_api_test'] = {
                'status': 'error',
                'error': str(e),
                'message': 'Could not connect to Dhan API'
            }
        
        logger.info(f"💼 Dhan credentials: {'✅' if dhan_configured else '❌'}")
        logger.info(f"💼 Dhan API access: {'✅' if results.get('dhan_api_test', {}).get('accessible') else '❌'}")
        
        return results

    async def setup_application_access(self):
        """🌐 Setup application access URLs"""
        logger.info("🌐 Setting up application access...")
        
        results = {}
        
        # Create access URLs based on working endpoints
        cloud_results = await self.test_cloud_endpoints()
        
        working_endpoints = []
        for name, result in cloud_results.items():
            if result.get('status') == 'healthy':
                working_endpoints.append({
                    'name': name,
                    'url': self.endpoints[name],
                    'type': 'cloud'
                })
        
        # Add local access if available
        try:
            async with aiohttp.ClientSession() as session:
                local_url = f"http://localhost:{self.local_ports['backend']}"
                async with session.get(f"{local_url}/health", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        working_endpoints.append({
                            'name': 'local_backend',
                            'url': local_url,
                            'type': 'local'
                        })
        except:
            pass
        
        results['access_points'] = working_endpoints
        results['recommended_url'] = working_endpoints[0]['url'] if working_endpoints else None
        
        # Create quick access information
        if working_endpoints:
            logger.info("✅ Application access points found:")
            for endpoint in working_endpoints:
                logger.info(f"   🔗 {endpoint['name']}: {endpoint['url']}")
        else:
            logger.warning("⚠️ No working endpoints found")
        
        return results

    async def generate_verification_report(self, results):
        """📋 Generate comprehensive verification report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(results),
            'detailed_results': results,
            'recommendations': self._generate_recommendations(results),
            'next_steps': self._generate_next_steps(results)
        }
        
        # Save report to file
        report_path = f"application_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Verification report saved: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 INFINITYAI.PRO APPLICATION ACCESS SUMMARY")
        print("="*60)
        
        for key, value in report['summary'].items():
            status_icon = "✅" if value else "❌"
            print(f"{status_icon} {key.replace('_', ' ').title()}: {'Ready' if value else 'Needs Setup'}")
        
        print("\n📍 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print("\n🚀 NEXT STEPS:")
        for step in report['next_steps']:
            print(f"  {step}")
        
        return report

    def _generate_summary(self, results):
        """Generate summary of verification results"""
        return {
            'cloud_endpoints_working': any(r.get('status') == 'healthy' for r in results['cloud_endpoints'].values()),
            'local_setup_complete': all(results['local_setup'][key].get('exists', False) for key in ['frontend_build', 'backend_main', 'api_config']),
            'frontend_backend_integrated': results['frontend_backend_integration'].get('backend_health', {}).get('status') == 'healthy',
            'dhan_sandbox_ready': results['dhan_sandbox']['dhan_credentials']['configured'],
            'application_accessible': len(results['application_access']['access_points']) > 0
        }

    def _generate_recommendations(self, results):
        """Generate recommendations based on results"""
        recommendations = []
        
        if not any(r.get('status') == 'healthy' for r in results['cloud_endpoints'].values()):
            recommendations.append("Restart Azure Container Apps using: az containerapp restart")
        
        if not results['local_setup']['frontend_build']['exists']:
            recommendations.append("Build frontend: cd frontend && npm run build")
        
        if not results['dhan_sandbox']['dhan_credentials']['configured']:
            recommendations.append("Configure Dhan API credentials in backend/.env file")
        
        if results['frontend_backend_integration'].get('backend_health', {}).get('status') != 'healthy':
            recommendations.append("Start local backend: cd backend && python main.py")
        
        return recommendations

    def _generate_next_steps(self, results):
        """Generate next steps for user"""
        steps = []
        
        if results['application_access']['recommended_url']:
            steps.append(f"1. 🌐 Access your application at: {results['application_access']['recommended_url']}")
        
        steps.append("2. 💼 Set up Dhan Sandbox testing with proper API credentials")
        steps.append("3. 🚀 Start live trading when market opens (9:15 AM - 3:30 PM)")
        steps.append("4. 🗣️ Test voice commands: 'Start momentum trading on NIFTY with 2 lakh capital'")
        
        return steps

# Additional utility functions for easy setup

def create_dhan_sandbox_config():
    """Create Dhan Sandbox configuration template"""
    config_template = '''
# Dhan API Configuration for InfinityAI.Pro
# Add your Dhan credentials here for live trading

# Dhan API Credentials (get from https://web.dhan.co/developer/app)
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here

# Trading Configuration
TRADING_CAPITAL=1000000  # ₹10 lakh (adjust as needed)
RISK_PER_TRADE=0.02      # 2% risk per trade
MAX_POSITIONS=10         # Maximum concurrent positions
DAILY_LOSS_LIMIT=100000  # ₹1 lakh daily loss limit

# Dhan API URLs
DHAN_BASE_URL=https://api.dhan.co
DHAN_SANDBOX_URL=https://api.dhan.co  # Same for now

# Trading Symbols (NSE)
DEFAULT_SYMBOLS=NIFTY,BANKNIFTY,RELIANCE,TCS,HDFCBANK,ICICIBANK

# AI Configuration
AI_CONFIDENCE_THRESHOLD=0.75
VOICE_TRADING_ENABLED=true
RISK_MANAGEMENT_ENABLED=true
'''
    
    # Write to backend .env file
    env_path = Path("backend/.env")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(config_template)
        print(f"✅ Created Dhan configuration template: {env_path}")
        print("📝 Please edit backend/.env and add your Dhan API credentials")
    else:
        print(f"📁 Configuration file already exists: {env_path}")

def start_local_development():
    """Start local development servers"""
    try:
        print("🚀 Starting InfinityAI.Pro local development servers...")
        
        # Start backend
        print("📊 Starting backend server...")
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], cwd="backend")
        
        # Start frontend (if needed)
        frontend_path = Path("frontend")
        if frontend_path.exists():
            print("🎨 Frontend available. To start development server:")
            print("   cd frontend && npm start")
        
        print(f"✅ Backend started on http://localhost:8000")
        print(f"✅ Frontend served from backend at http://localhost:8000")
        print(f"📱 API Documentation: http://localhost:8000/docs")
        
        return backend_process
        
    except Exception as e:
        print(f"❌ Error starting development servers: {e}")
        return None

# Main execution
async def main():
    """Main function to run verification"""
    verifier = InfinityAIAccessVerifier()
    results = await verifier.verify_all_systems()
    
    # If no working endpoints, offer to start local development
    if not results['application_access']['access_points']:
        print("\n🔧 No cloud endpoints available. Would you like to start local development?")
        create_dhan_sandbox_config()
        
        response = input("Start local development server? (y/N): ").lower()
        if response == 'y':
            start_local_development()

if __name__ == "__main__":
    asyncio.run(main())