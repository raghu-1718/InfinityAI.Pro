#!/usr/bin/env python3
"""
InfinityAI.Pro - Real-time Infrastructure & Performance Verification
Complete deployment footprint, performance metrics, and live data validation
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InfrastructureVerifier:
    def __init__(self):
        # Production service endpoints
        self.services = {
            'frontend': {
                'url': 'https://infinityai-pro-frontend-573866363639.us-central1.run.app',
                'type': 'React Frontend',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            },
            'engine_a': {
                'url': 'https://engine-a-573866363639-573866363639.us-central1.run.app',
                'type': 'Market Data Service',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            },
            'engine_b': {
                'url': 'https://engine-b-573866363639-573866363639.us-central1.run.app',
                'type': 'AI/ML Service',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            },
            'engine_c': {
                'url': 'https://engine-c-573866363639-573866363639.us-central1.run.app',
                'type': 'Trade Execution & OAuth',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            },
            'engine_d': {
                'url': 'https://engine-d-573866363639-573866363639.us-central1.run.app',
                'type': 'Chatbot & Coordination',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            },
            'engine_ultra': {
                'url': 'https://engine-ultra-573866363639-573866363639.us-central1.run.app',
                'type': 'Ultra Aggressive Trading',
                'region': 'us-central1',
                'platform': 'Cloud Run'
            }
        }
        
        # Performance test configurations
        self.test_duration = 30  # seconds
        self.concurrent_requests = 10
        self.request_interval = 0.1  # 100ms between requests
        
        logger.info("🔍 Infrastructure Verifier Initialized")
    
    async def get_cloud_run_service_details(self, service_name: str) -> Dict[str, Any]:
        """Get Cloud Run service deployment details"""
        try:
            # Use gcloud CLI to get service details
            cmd = f"gcloud run services describe {service_name} --region=us-central1 --format=json"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                service_info = json.loads(stdout.decode())
                
                # Extract key deployment information
                spec = service_info.get('spec', {})
                status = service_info.get('status', {})
                metadata = service_info.get('metadata', {})
                
                template = spec.get('template', {})
                container_spec = template.get('spec', {}).get('containers', [{}])[0]
                
                return {
                    'service_name': service_name,
                    'region': metadata.get('labels', {}).get('cloud.googleapis.com/location', 'us-central1'),
                    'created': metadata.get('creationTimestamp'),
                    'last_modified': status.get('latestCreatedRevisionName', ''),
                    'url': status.get('url', ''),
                    'container_image': container_spec.get('image', 'unknown'),
                    'cpu_limit': container_spec.get('resources', {}).get('limits', {}).get('cpu', 'unknown'),
                    'memory_limit': container_spec.get('resources', {}).get('limits', {}).get('memory', 'unknown'),
                    'concurrency': spec.get('template', {}).get('spec', {}).get('containerConcurrency', 'unknown'),
                    'min_instances': spec.get('template', {}).get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/minScale', '0'),
                    'max_instances': spec.get('template', {}).get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/maxScale', 'unknown'),
                    'timeout': spec.get('template', {}).get('spec', {}).get('timeoutSeconds', 'unknown'),
                    'traffic': status.get('traffic', []),
                    'conditions': status.get('conditions', [])
                }
            else:
                logger.error(f"Failed to get service details for {service_name}: {stderr.decode()}")
                return {'error': stderr.decode(), 'service_name': service_name}
                
        except Exception as e:
            logger.error(f"Error getting Cloud Run details for {service_name}: {e}")
            return {'error': str(e), 'service_name': service_name}
    
    async def measure_response_time(self, url: str, endpoint: str = "", timeout: int = 10) -> Dict[str, Any]:
        """Measure response time for a specific endpoint"""
        full_url = f"{url}{endpoint}"
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(full_url) as response:
                    await response.text()  # Ensure full response is received
                    end_time = time.time()
                    
                    return {
                        'url': full_url,
                        'status_code': response.status,
                        'response_time_ms': round((end_time - start_time) * 1000, 2),
                        'success': response.status < 400,
                        'headers': dict(response.headers)
                    }
        except asyncio.TimeoutError:
            return {
                'url': full_url,
                'status_code': 408,
                'response_time_ms': timeout * 1000,
                'success': False,
                'error': 'timeout'
            }
        except Exception as e:
            return {
                'url': full_url,
                'status_code': 0,
                'response_time_ms': 0,
                'success': False,
                'error': str(e)
            }
    
    async def load_test_service(self, service_name: str, url: str, endpoint: str = "/health") -> Dict[str, Any]:
        """Perform load testing on a service to measure throughput and capacity"""
        logger.info(f"🚀 Load testing {service_name} for {self.test_duration}s...")
        
        results = []
        start_time = time.time()
        error_count = 0
        
        async def make_request():
            nonlocal error_count
            try:
                result = await self.measure_response_time(url, endpoint)
                if not result['success']:
                    error_count += 1
                return result
            except Exception as e:
                error_count += 1
                return {'success': False, 'error': str(e)}
        
        # Concurrent requests over test duration
        tasks = []
        while (time.time() - start_time) < self.test_duration:
            for _ in range(self.concurrent_requests):
                tasks.append(make_request())
            
            if len(tasks) >= 100:  # Process in batches
                batch_results = await asyncio.gather(*tasks)
                results.extend([r for r in batch_results if r.get('response_time_ms')])
                tasks = []
            
            await asyncio.sleep(self.request_interval)
        
        # Process remaining tasks
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            results.extend([r for r in batch_results if r.get('response_time_ms')])
        
        # Calculate statistics
        if results:
            response_times = [r['response_time_ms'] for r in results if r.get('response_time_ms')]
            success_count = sum(1 for r in results if r.get('success'))
            
            total_requests = len(results)
            elapsed_time = time.time() - start_time
            
            return {
                'service_name': service_name,
                'test_duration_s': round(elapsed_time, 2),
                'total_requests': total_requests,
                'successful_requests': success_count,
                'failed_requests': total_requests - success_count,
                'error_rate_percent': round((error_count / total_requests) * 100, 2) if total_requests > 0 else 0,
                'requests_per_second': round(total_requests / elapsed_time, 2),
                'avg_response_time_ms': round(statistics.mean(response_times), 2) if response_times else 0,
                'median_response_time_ms': round(statistics.median(response_times), 2) if response_times else 0,
                'p95_response_time_ms': round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 20 else 0,
                'p99_response_time_ms': round(statistics.quantiles(response_times, n=100)[98], 2) if len(response_times) > 100 else 0,
                'min_response_time_ms': min(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0
            }
        else:
            return {
                'service_name': service_name,
                'error': 'No successful responses received',
                'total_requests': 0,
                'error_rate_percent': 100
            }
    
    async def verify_real_time_data_flow(self) -> Dict[str, Any]:
        """Verify real-time data flow across all services"""
        logger.info("📊 Verifying real-time data flow...")
        
        data_flow_results = {}
        
        # Test market data pipeline
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                # 1. Test Engine A market signals
                async with session.get(f"{self.services['engine_a']['url']}/api/signals") as response:
                    if response.status == 200:
                        data = await response.json()
                        data_flow_results['market_data'] = {
                            'status': 'active',
                            'signals_generated': data.get('count', 0),
                            'last_update': data.get('timestamp'),
                            'data_quality': 'live' if data.get('signals') else 'static'
                        }
                
                # 2. Test Engine B AI predictions
                async with session.get(f"{self.services['engine_b']['url']}/api/ai-signals") as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_signals = data.get('ai_signals', [])
                        data_flow_results['ai_predictions'] = {
                            'status': 'generating',
                            'models_active': len(ai_signals),
                            'confidence_avg': round(sum(s.get('confidence', 0) for s in ai_signals) / len(ai_signals), 2) if ai_signals else 0,
                            'prediction_quality': 'real-time' if ai_signals else 'static'
                        }
                
                # 3. Test Engine C trading execution
                test_order = {
                    "symbol": "TEST",
                    "quantity": 1,
                    "order_type": "BUY",
                    "price": 100
                }
                async with session.post(f"{self.services['engine_c']['url']}/api/orders", json=test_order) as response:
                    if response.status == 200:
                        data = await response.json()
                        data_flow_results['trading_execution'] = {
                            'status': 'operational',
                            'order_processing': 'active',
                            'demo_mode': 'demo mode' in data.get('message', '').lower(),
                            'response_time_ms': 0  # Will be measured separately
                        }
                
                # 4. Test Engine D chatbot coordination
                chat_test = {
                    "user_id": "load-test-user",
                    "message": "System status check"
                }
                async with session.post(f"{self.services['engine_d']['url']}/api/chat", json=chat_test) as response:
                    if response.status == 200:
                        data = await response.json()
                        data_flow_results['chatbot_coordination'] = {
                            'status': 'responsive',
                            'intent_recognition': data.get('intent'),
                            'confidence': data.get('confidence'),
                            'multi_engine_comm': len(data.get('response', '')) > 50
                        }
                
                # 5. Test OAuth integration
                async with session.get(f"{self.services['engine_c']['url']}/api/dhan/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        data_flow_results['oauth_integration'] = {
                            'status': 'configured',
                            'endpoints_active': bool(data.get('oauth_endpoint')),
                            'connected_users': data.get('connected_users', 0)
                        }
        
        except Exception as e:
            logger.error(f"Error verifying data flow: {e}")
            data_flow_results['error'] = str(e)
        
        return data_flow_results
    
    async def check_service_uptime(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check service uptime and availability"""
        try:
            # Multiple health checks over time
            health_checks = []
            for _ in range(5):
                result = await self.measure_response_time(url, "/health" if "engine" in service_name else "")
                health_checks.append(result['success'])
                await asyncio.sleep(1)
            
            availability = (sum(health_checks) / len(health_checks)) * 100
            
            return {
                'service_name': service_name,
                'availability_percent': round(availability, 2),
                'status': 'healthy' if availability >= 80 else 'degraded' if availability >= 50 else 'critical',
                'consecutive_health_checks': health_checks
            }
        except Exception as e:
            return {
                'service_name': service_name,
                'availability_percent': 0,
                'status': 'error',
                'error': str(e)
            }
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive real-time verification report"""
        logger.info("📋 Generating comprehensive infrastructure report...")
        
        report = {
            'verification_timestamp': datetime.now().isoformat(),
            'test_configuration': {
                'test_duration_seconds': self.test_duration,
                'concurrent_requests': self.concurrent_requests,
                'request_interval_ms': self.request_interval * 1000
            },
            'deployment_details': {},
            'performance_metrics': {},
            'uptime_status': {},
            'data_flow_validation': {},
            'integration_health': {}
        }
        
        # Get deployment details for all services
        logger.info("🔍 Gathering deployment details...")
        deployment_tasks = []
        for service_name, service_info in self.services.items():
            if service_name != 'frontend':  # Frontend doesn't have a direct Cloud Run service name
                cloud_run_name = service_name.replace('_', '-') + '-573866363639'
                deployment_tasks.append(self.get_cloud_run_service_details(cloud_run_name))
        
        deployment_results = await asyncio.gather(*deployment_tasks, return_exceptions=True)
        
        # Process deployment results
        for i, result in enumerate(deployment_results):
            service_name = list(self.services.keys())[i+1]  # Skip frontend
            if isinstance(result, dict) and 'error' not in result:
                report['deployment_details'][service_name] = result
            else:
                report['deployment_details'][service_name] = {'error': str(result)}
        
        # Performance testing
        logger.info("⚡ Running performance tests...")
        performance_tasks = []
        for service_name, service_info in self.services.items():
            endpoint = "/health" if service_name != 'frontend' else ""
            performance_tasks.append(self.load_test_service(service_name, service_info['url'], endpoint))
        
        performance_results = await asyncio.gather(*performance_tasks)
        for result in performance_results:
            if result.get('service_name'):
                report['performance_metrics'][result['service_name']] = result
        
        # Uptime verification
        logger.info("⏱️ Checking service uptime...")
        uptime_tasks = []
        for service_name, service_info in self.services.items():
            uptime_tasks.append(self.check_service_uptime(service_name, service_info['url']))
        
        uptime_results = await asyncio.gather(*uptime_tasks)
        for result in uptime_results:
            if result.get('service_name'):
                report['uptime_status'][result['service_name']] = result
        
        # Data flow validation
        report['data_flow_validation'] = await self.verify_real_time_data_flow()
        
        # Calculate overall system health
        healthy_services = sum(1 for status in report['uptime_status'].values() 
                             if status.get('status') in ['healthy'])
        total_services = len(report['uptime_status'])
        
        report['system_summary'] = {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'system_health_percent': round((healthy_services / total_services) * 100, 2) if total_services > 0 else 0,
            'overall_status': self._determine_overall_status(report),
            'avg_response_time_ms': self._calculate_avg_response_time(report['performance_metrics']),
            'total_rps_capacity': self._calculate_total_rps(report['performance_metrics']),
            'avg_error_rate_percent': self._calculate_avg_error_rate(report['performance_metrics'])
        }
        
        return report
    
    def _determine_overall_status(self, report: Dict) -> str:
        """Determine overall system status"""
        health_percent = report.get('system_summary', {}).get('system_health_percent', 0)
        
        if health_percent >= 90:
            return 'EXCELLENT'
        elif health_percent >= 80:
            return 'OPERATIONAL'
        elif health_percent >= 60:
            return 'DEGRADED'
        else:
            return 'CRITICAL'
    
    def _calculate_avg_response_time(self, performance_metrics: Dict) -> float:
        """Calculate average response time across all services"""
        response_times = [metrics.get('avg_response_time_ms', 0) 
                         for metrics in performance_metrics.values() 
                         if isinstance(metrics.get('avg_response_time_ms'), (int, float))]
        return round(statistics.mean(response_times), 2) if response_times else 0
    
    def _calculate_total_rps(self, performance_metrics: Dict) -> float:
        """Calculate total RPS capacity across all services"""
        rps_values = [metrics.get('requests_per_second', 0) 
                     for metrics in performance_metrics.values() 
                     if isinstance(metrics.get('requests_per_second'), (int, float))]
        return round(sum(rps_values), 2)
    
    def _calculate_avg_error_rate(self, performance_metrics: Dict) -> float:
        """Calculate average error rate across all services"""
        error_rates = [metrics.get('error_rate_percent', 0) 
                      for metrics in performance_metrics.values() 
                      if isinstance(metrics.get('error_rate_percent'), (int, float))]
        return round(statistics.mean(error_rates), 2) if error_rates else 0

async def main():
    """Main verification execution"""
    print("🔍 Starting Real-time Infrastructure Verification")
    print("=" * 80)
    
    verifier = InfrastructureVerifier()
    
    try:
        # Generate comprehensive report
        report = await verifier.generate_comprehensive_report()
        
        # Display key results
        system_summary = report['system_summary']
        print(f"\n📊 SYSTEM HEALTH: {system_summary['overall_status']} ({system_summary['system_health_percent']}%)")
        print(f"🚀 Total Services: {system_summary['total_services']}")
        print(f"✅ Healthy Services: {system_summary['healthy_services']}")
        print(f"⚡ Average Response Time: {system_summary['avg_response_time_ms']}ms")
        print(f"🔄 Total RPS Capacity: {system_summary['total_rps_capacity']}")
        print(f"❌ Average Error Rate: {system_summary['avg_error_rate_percent']}%")
        
        # Service-by-service summary
        print(f"\n🔍 SERVICE STATUS:")
        for service_name, uptime_info in report['uptime_status'].items():
            perf_info = report['performance_metrics'].get(service_name, {})
            status_emoji = "✅" if uptime_info.get('status') == 'healthy' else "❌"
            availability = uptime_info.get('availability_percent', 0)
            rps = perf_info.get('requests_per_second', 0)
            avg_time = perf_info.get('avg_response_time_ms', 0)
            
            print(f"  {status_emoji} {service_name.upper()}: {availability}% uptime, {rps} RPS, {avg_time}ms avg")
        
        # Data flow status
        print(f"\n📊 DATA FLOW STATUS:")
        data_flow = report['data_flow_validation']
        for component, status in data_flow.items():
            if isinstance(status, dict) and 'status' in status:
                print(f"  📈 {component.replace('_', ' ').title()}: {status['status']}")
        
        # Save detailed report
        report_filename = f"infrastructure_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_filename}")
        print(f"\n🎯 REAL-TIME VERIFICATION COMPLETE")
        print("=" * 80)
        
        return report
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"❌ Verification failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())