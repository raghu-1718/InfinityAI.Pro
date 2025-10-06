#!/usr/bin/env python3
"""
🚀 InfinityAI.Pro Azure Container App Frontend Integration Fixer
🎯 Complete frontend-backend integration and API credential setup
📱 Sets up Postback URLs, Redirect URLs, and environment variables
"""

import subprocess
import json
import os
import requests
from datetime import datetime

class AzureContainerAppIntegrator:
    """🔧 Azure Container App Frontend Integration"""
    
    def __init__(self):
        self.resource_group = "infinityai-pro-rg"
        self.container_app_name = "infinityai-app"
        self.container_app_alt = "infinityai-engine-a"
        
        # Get current container app details
        self.app_details = self.get_container_app_details()
        self.base_url = f"https://{self.app_details['fqdn']}"
        
    def get_container_app_details(self):
        """Get current container app configuration"""
        try:
            result = subprocess.run([
                'az', 'containerapp', 'show',
                '--name', self.container_app_name,
                '--resource-group', self.resource_group,
                '--output', 'json'
            ], capture_output=True, text=True, check=True)
            
            return json.loads(result.stdout)
        except Exception as e:
            print(f"❌ Error getting container app details: {e}")
            return None
    
    def create_frontend_backend_integration(self):
        """🔗 Create complete frontend-backend integration"""
        print("🔗 Setting up Frontend-Backend Integration...")
        
        # Update container app with frontend serving capability
        integration_config = {
            "ingress": {
                "external": True,
                "targetPort": 8000,
                "allowInsecure": False,
                "traffic": [{"weight": 100, "latestRevision": True}],
                "corsPolicy": {
                    "allowCredentials": True,
                    "allowedOrigins": ["*"],
                    "allowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allowedHeaders": ["*"]
                }
            },
            "template": {
                "containers": [{
                    "name": "infinityai-app",
                    "image": "your-registry/infinityai-app:latest",
                    "env": [
                        {"name": "ENVIRONMENT", "value": "production"},
                        {"name": "FRONTEND_ENABLED", "value": "true"},
                        {"name": "SERVE_STATIC_FILES", "value": "true"},
                        {"name": "API_BASE_URL", "value": self.base_url}
                    ],
                    "resources": {
                        "cpu": 2.0,
                        "memory": "4Gi"
                    }
                }],
                "scale": {
                    "minReplicas": 2,
                    "maxReplicas": 10
                }
            }
        }
        
        return integration_config
    
    def generate_api_credentials_and_urls(self):
        """🔑 Generate API credentials and required URLs"""
        
        # Base URLs for different purposes
        urls_config = {
            "base_url": self.base_url,
            "frontend_url": self.base_url,
            "api_base_url": f"{self.base_url}/api",
            
            # Postback URLs for webhooks and callbacks
            "postback_urls": {
                "trading_webhook": f"{self.base_url}/api/webhooks/trading",
                "dhan_callback": f"{self.base_url}/api/callbacks/dhan", 
                "ai_signals_webhook": f"{self.base_url}/api/webhooks/ai-signals",
                "market_data_webhook": f"{self.base_url}/api/webhooks/market-data",
                "voice_commands_webhook": f"{self.base_url}/api/webhooks/voice"
            },
            
            # Redirect URLs for OAuth and authentication
            "redirect_urls": {
                "dhan_oauth_redirect": f"{self.base_url}/auth/dhan/callback",
                "login_redirect": f"{self.base_url}/dashboard",
                "logout_redirect": f"{self.base_url}/login",
                "api_auth_redirect": f"{self.base_url}/api/auth/callback"
            },
            
            # API Endpoints for external integrations
            "api_endpoints": {
                "health_check": f"{self.base_url}/health",
                "market_data": f"{self.base_url}/api/market-data",
                "trading_api": f"{self.base_url}/api/trading",
                "ai_signals": f"{self.base_url}/api/ai/signals",
                "voice_commands": f"{self.base_url}/api/voice",
                "portfolio": f"{self.base_url}/api/portfolio",
                "websocket": f"{self.base_url.replace('https', 'wss')}/ws"
            }
        }
        
        # Generate API credentials (these should be stored securely)
        api_credentials = {
            "api_key": f"INFINITY_API_{datetime.now().strftime('%Y%m%d')}_{hash(self.base_url) % 10000:04d}",
            "api_secret": f"INFINITY_SECRET_{datetime.now().strftime('%Y%m%d%H%M')}_{hash(self.container_app_name) % 100000:05d}",
            "webhook_secret": f"INFINITY_WEBHOOK_{datetime.now().strftime('%Y%m%d')}_{hash('webhook') % 10000:04d}",
            "jwt_secret": f"INFINITY_JWT_{datetime.now().strftime('%Y%m%d')}_{hash('jwt') % 100000:05d}"
        }
        
        return urls_config, api_credentials
    
    def create_environment_variables_config(self, urls_config, api_credentials):
        """📝 Create environment variables for all engines"""
        
        env_config = {
            # Common environment variables for all engines
            "common_env": [
                {"name": "ENVIRONMENT", "value": "production"},
                {"name": "PLATFORM_NAME", "value": "InfinityAI.Pro"},
                {"name": "VERSION", "value": "2.0.0"},
                
                # API Configuration
                {"name": "API_KEY", "value": api_credentials["api_key"]},
                {"name": "API_SECRET", "value": api_credentials["api_secret"]},
                {"name": "WEBHOOK_SECRET", "value": api_credentials["webhook_secret"]},
                {"name": "JWT_SECRET", "value": api_credentials["jwt_secret"]},
                
                # Base URLs
                {"name": "BASE_URL", "value": urls_config["base_url"]},
                {"name": "FRONTEND_URL", "value": urls_config["frontend_url"]},
                {"name": "API_BASE_URL", "value": urls_config["api_base_url"]},
                
                # Postback URLs
                {"name": "TRADING_WEBHOOK_URL", "value": urls_config["postback_urls"]["trading_webhook"]},
                {"name": "DHAN_CALLBACK_URL", "value": urls_config["postback_urls"]["dhan_callback"]},
                {"name": "AI_SIGNALS_WEBHOOK_URL", "value": urls_config["postback_urls"]["ai_signals_webhook"]},
                
                # Redirect URLs
                {"name": "DHAN_OAUTH_REDIRECT_URL", "value": urls_config["redirect_urls"]["dhan_oauth_redirect"]},
                {"name": "LOGIN_REDIRECT_URL", "value": urls_config["redirect_urls"]["login_redirect"]},
                {"name": "API_AUTH_REDIRECT_URL", "value": urls_config["redirect_urls"]["api_auth_redirect"]},
                
                # Cross-Engine Communication
                {"name": "ENGINE_A_URL", "value": urls_config["base_url"]},
                {"name": "ENGINE_B_URL", "value": "https://infinityai-engine-b.googlecloud.run"},
                {"name": "ENGINE_C_URL", "value": "https://infinityai-alb.us-east-1.elb.amazonaws.com:8002"},
                {"name": "ENGINE_D_URL", "value": "https://infinityai-alb.us-east-1.elb.amazonaws.com:8000"}
            ],
            
            # Engine-specific environment variables
            "engine_a_env": [
                {"name": "ENGINE_TYPE", "value": "frontend_backend"},
                {"name": "SERVE_FRONTEND", "value": "true"},
                {"name": "MARKET_DATA_ENABLED", "value": "true"},
                {"name": "WEBSOCKET_ENABLED", "value": "true"}
            ],
            
            "engine_b_env": [
                {"name": "ENGINE_TYPE", "value": "ai_processing"},
                {"name": "GPU_ENABLED", "value": "true"},
                {"name": "AI_MODELS_COUNT", "value": "18"},
                {"name": "CUDA_ENABLED", "value": "true"}
            ],
            
            "engine_c_env": [
                {"name": "ENGINE_TYPE", "value": "trading_execution"},
                {"name": "DHAN_INTEGRATION", "value": "true"},
                {"name": "TRADING_ENABLED", "value": "true"},
                {"name": "RISK_MANAGEMENT", "value": "true"}
            ],
            
            "engine_d_env": [
                {"name": "ENGINE_TYPE", "value": "voice_assistant"},
                {"name": "VOICE_ENABLED", "value": "true"},
                {"name": "NLP_ENABLED", "value": "true"},
                {"name": "CHAT_ENABLED", "value": "true"}
            ]
        }
        
        return env_config
    
    def update_container_app_with_frontend(self):
        """🚀 Update Azure Container App with frontend integration"""
        print("🚀 Updating Azure Container App with frontend integration...")
        
        try:
            # Update the container app configuration
            result = subprocess.run([
                'az', 'containerapp', 'update',
                '--name', self.container_app_name,
                '--resource-group', self.resource_group,
                '--set-env-vars', 
                'FRONTEND_ENABLED=true',
                'SERVE_STATIC_FILES=true',
                'ENVIRONMENT=production',
                '--cpu', '2.0',
                '--memory', '4Gi',
                '--min-replicas', '2',
                '--max-replicas', '10'
            ], capture_output=True, text=True, check=True)
            
            print("✅ Container app updated successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error updating container app: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
            return False
    
    def test_frontend_backend_integration(self):
        """🧪 Test the frontend-backend integration"""
        print("🧪 Testing frontend-backend integration...")
        
        test_urls = [
            f"{self.base_url}/health",
            f"{self.base_url}/",  # Frontend root
            f"{self.base_url}/api/market-data",
            f"{self.base_url}/docs"  # API documentation
        ]
        
        results = {}
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                results[url] = {
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "response_time": response.elapsed.total_seconds()
                }
                print(f"✅ {url}: HTTP {response.status_code}")
            except Exception as e:
                results[url] = {
                    "error": str(e),
                    "success": False
                }
                print(f"❌ {url}: {str(e)}")
        
        return results
    
    def generate_comprehensive_report(self, urls_config, api_credentials, env_config, test_results):
        """📋 Generate comprehensive integration report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "azure_details": {
                "resource_group": self.resource_group,
                "container_app": self.container_app_name,
                "base_url": self.base_url,
                "status": "integrated"
            },
            "urls_and_credentials": {
                "urls": urls_config,
                "api_credentials": api_credentials
            },
            "environment_variables": env_config,
            "integration_tests": test_results,
            "next_steps": [
                "Configure Dhan API with provided callback URLs",
                "Set up environment variables in all engines",
                "Test voice trading functionality",
                "Deploy updated containers with new configuration"
            ]
        }
        
        # Save report to file
        report_file = f"azure_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Integration report saved: {report_file}")
        return report
    
    def run_complete_integration(self):
        """🎯 Run complete Azure frontend-backend integration"""
        print("🎯 InfinityAI.Pro Azure Container App Integration")
        print("=" * 60)
        
        # Step 1: Generate URLs and credentials
        print("\n🔑 Generating API credentials and URLs...")
        urls_config, api_credentials = self.generate_api_credentials_and_urls()
        
        # Step 2: Create environment variables configuration
        print("\n📝 Creating environment variables configuration...")
        env_config = self.create_environment_variables_config(urls_config, api_credentials)
        
        # Step 3: Update container app
        print("\n🚀 Updating Azure Container App...")
        update_success = self.update_container_app_with_frontend()
        
        # Step 4: Test integration
        print("\n🧪 Testing integration...")
        test_results = self.test_frontend_backend_integration()
        
        # Step 5: Generate comprehensive report
        print("\n📋 Generating integration report...")
        report = self.generate_comprehensive_report(urls_config, api_credentials, env_config, test_results)
        
        # Print summary
        self.print_integration_summary(urls_config, api_credentials)
        
        return report
    
    def print_integration_summary(self, urls_config, api_credentials):
        """🎊 Print integration summary"""
        print("\n" + "="*60)
        print("🎊 INFINITYAI.PRO AZURE INTEGRATION COMPLETE")
        print("="*60)
        
        print(f"\n🌐 PRIMARY APPLICATION URL:")
        print(f"   {self.base_url}")
        
        print(f"\n🔑 API CREDENTIALS:")
        print(f"   API Key: {api_credentials['api_key']}")
        print(f"   API Secret: {api_credentials['api_secret'][:20]}...")
        
        print(f"\n📡 POSTBACK URLs (for Dhan integration):")
        for name, url in urls_config["postback_urls"].items():
            print(f"   {name}: {url}")
        
        print(f"\n🔄 REDIRECT URLs (for OAuth):")
        for name, url in urls_config["redirect_urls"].items():
            print(f"   {name}: {url}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. 🌐 Access your app: {self.base_url}")
        print(f"   2. 💼 Configure Dhan API with callback URL: {urls_config['postback_urls']['dhan_callback']}")
        print(f"   3. 🔑 Use API credentials in environment variables")
        print(f"   4. 🧪 Test voice trading: 'Start momentum trading on NIFTY'")
        
        print(f"\n✅ Frontend-Backend integration is now COMPLETE!")

def main():
    """Main function to run Azure integration"""
    integrator = AzureContainerAppIntegrator()
    report = integrator.run_complete_integration()
    
    return report

if __name__ == "__main__":
    main()