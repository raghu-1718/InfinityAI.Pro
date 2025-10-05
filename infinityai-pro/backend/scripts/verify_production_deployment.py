#!/usr/bin/env python3
"""
InfinityAI.Pro Production Deployment Verification Script
Comprehensive end-to-end testing of all services, APIs, and functionality
"""

import os
import sys
import json
import time
import asyncio
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from engines.shared.data_api_integrator import DataAPIIntegrator
    from strategies.giftnifty_momentum_ai import GiftNiftyMomentumAI
    from config import Config
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the backend directory")
    sys.exit(1)

class ProductionVerifier:
    def __init__(self):
        self.config = Config()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'overall_status': 'UNKNOWN',
            'summary': {}
        }
        self.data_integrator = None
        self.strategy = None
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with colors and timestamps"""
        colors = {
            'INFO': '\033[0;34m',     # Blue
            'SUCCESS': '\033[0;32m',  # Green
            'WARNING': '\033[1;33m',  # Yellow
            'ERROR': '\033[0;31m',    # Red
            'CRITICAL': '\033[1;31m', # Bold Red
            'RESET': '\033[0m'        # Reset
        }
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = colors.get(level, colors['INFO'])
        reset = colors['RESET']
        
        icon = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(level, 'ℹ️')
        
        print(f"{color}[{timestamp}] {icon} {level}: {message}{reset}")
        
    def test_result(self, test_name: str, passed: bool, details: Dict[str, Any] = None):
        """Record test result"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results['tests'].append(result)
        
        if passed:
            self.log(f"{test_name}: PASSED", "SUCCESS")
        else:
            self.log(f"{test_name}: FAILED", "ERROR")
            
        return passed

    async def test_environment_setup(self) -> bool:
        """Test 1: Environment and Configuration"""
        self.log("🔧 Testing Environment Setup...", "INFO")
        
        try:
            # Check if all required environment variables are set
            required_vars = [
                'DHAN_CLIENT_ID', 'DHAN_ACCESS_TOKEN', 'AWS_ACCESS_KEY_ID',
                'DATABASE_URL', 'JWT_SECRET'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return self.test_result(
                    "Environment Variables", 
                    False, 
                    {'missing_variables': missing_vars}
                )
            
            # Test configuration loading
            config_data = {
                'dhan_client_id': self.config.DHAN_CLIENT_ID,
                'aws_region': self.config.AWS_REGION,
                'database_configured': bool(self.config.DATABASE_URL),
                'environment': self.config.ENVIRONMENT
            }
            
            return self.test_result(
                "Environment Variables", 
                True, 
                config_data
            )
            
        except Exception as e:
            return self.test_result(
                "Environment Variables", 
                False, 
                {'error': str(e)}
            )

    async def test_docker_services(self) -> bool:
        """Test 2: Docker Services Status"""
        self.log("🐳 Testing Docker Services...", "INFO")
        
        try:
            # Check if Docker is running
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                return self.test_result(
                    "Docker Services", 
                    False, 
                    {'error': 'Docker not running or not accessible'}
                )
            
            # Parse docker containers
            lines = result.stdout.strip().split('\n')
            containers = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        containers.append({
                            'name': parts[0],
                            'status': parts[1],
                            'ports': parts[2] if len(parts) > 2 else ''
                        })
            
            # Check for InfinityAI containers
            infinityai_containers = [c for c in containers if 'infinityai' in c['name'].lower()]
            
            return self.test_result(
                "Docker Services", 
                len(containers) > 0, 
                {
                    'total_containers': len(containers),
                    'infinityai_containers': len(infinityai_containers),
                    'running_containers': containers
                }
            )
            
        except Exception as e:
            return self.test_result(
                "Docker Services", 
                False, 
                {'error': str(e)}
            )

    async def test_dhan_api_connection(self) -> bool:
        """Test 3: Dhan API Connection and Data Fetching"""
        self.log("📈 Testing Dhan API Connection...", "INFO")
        
        try:
            # Initialize data integrator
            self.data_integrator = DataAPIIntegrator()
            
            # Test authentication
            auth_result = await self.data_integrator.test_authentication('dhan')
            
            if not auth_result:
                return self.test_result(
                    "Dhan API Authentication", 
                    False, 
                    {'error': 'Authentication failed'}
                )
            
            # Test market data fetching
            test_symbol = "NIFTY"
            
            # Fetch historical data
            self.log(f"Fetching historical data for {test_symbol}...", "INFO")
            historical_data = await self.data_integrator.get_historical_data(
                'dhan', test_symbol, '1D', 30
            )
            
            # Fetch option chain
            self.log(f"Fetching option chain for {test_symbol}...", "INFO")
            option_chain = await self.data_integrator.get_option_chain('dhan', test_symbol)
            
            # Fetch portfolio
            self.log("Fetching portfolio data...", "INFO")
            portfolio = await self.data_integrator.get_portfolio('dhan')
            
            details = {
                'authentication': 'SUCCESS',
                'historical_data_points': len(historical_data) if historical_data else 0,
                'option_chain_strikes': len(option_chain) if option_chain else 0,
                'portfolio_positions': len(portfolio) if portfolio else 0,
                'sample_data': {
                    'latest_price': historical_data[0] if historical_data else None,
                    'option_strikes': option_chain[:3] if option_chain else None
                }
            }
            
            success = all([
                historical_data and len(historical_data) > 0,
                option_chain is not None,
                portfolio is not None
            ])
            
            return self.test_result("Dhan API Data Fetching", success, details)
            
        except Exception as e:
            return self.test_result(
                "Dhan API Data Fetching", 
                False, 
                {'error': str(e)}
            )

    async def test_ai_strategy(self) -> bool:
        """Test 4: AI Strategy Functionality"""
        self.log("🧠 Testing AI Strategy (Gift Nifty Momentum)...", "INFO")
        
        try:
            # Initialize strategy
            self.strategy = GiftNiftyMomentumAI()
            
            # Test strategy initialization
            if not hasattr(self.strategy, 'models') or not self.strategy.models:
                return self.test_result(
                    "AI Strategy Initialization", 
                    False, 
                    {'error': 'Strategy models not initialized'}
                )
            
            # Test with sample data
            test_data = {
                'symbol': 'NIFTY',
                'current_price': 19500.0,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            # Generate signals
            self.log("Generating AI trading signals...", "INFO")
            signals = await self.strategy.generate_signals(test_data)
            
            # Test risk management
            portfolio_value = 25000  # As configured in strategy
            risk_metrics = await self.strategy.calculate_risk_metrics(
                test_data, portfolio_value
            )
            
            details = {
                'models_loaded': len(self.strategy.models) if hasattr(self.strategy, 'models') else 0,
                'signal_generated': signals is not None,
                'risk_calculated': risk_metrics is not None,
                'signals': signals,
                'risk_metrics': risk_metrics
            }
            
            success = signals is not None and risk_metrics is not None
            
            return self.test_result("AI Strategy Processing", success, details)
            
        except Exception as e:
            return self.test_result(
                "AI Strategy Processing", 
                False, 
                {'error': str(e)}
            )

    async def test_gpu_availability(self) -> bool:
        """Test 5: GPU Availability and CUDA Support"""
        self.log("🔥 Testing GPU Availability...", "INFO")
        
        try:
            # Check if NVIDIA-SMI is available
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', 
                     '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0:
                    gpu_info = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split(', ')
                            if len(parts) == 4:
                                gpu_info.append({
                                    'name': parts[0],
                                    'memory_total_mb': int(parts[1]),
                                    'memory_used_mb': int(parts[2]),
                                    'utilization_percent': int(parts[3])
                                })
                    
                    # Test CUDA availability in Python
                    cuda_available = False
                    try:
                        import torch
                        cuda_available = torch.cuda.is_available()
                        cuda_devices = torch.cuda.device_count() if cuda_available else 0
                    except ImportError:
                        try:
                            import tensorflow as tf
                            cuda_available = len(tf.config.list_physical_devices('GPU')) > 0
                            cuda_devices = len(tf.config.list_physical_devices('GPU'))
                        except ImportError:
                            cuda_devices = len(gpu_info)
                    
                    details = {
                        'nvidia_smi_available': True,
                        'gpu_count': len(gpu_info),
                        'cuda_available': cuda_available,
                        'cuda_devices': cuda_devices,
                        'gpu_details': gpu_info
                    }
                    
                    return self.test_result("GPU Availability", len(gpu_info) > 0, details)
                
            except FileNotFoundError:
                pass
            
            # Fallback: Check if running in Docker with GPU support
            try:
                result = subprocess.run(
                    ['docker', 'run', '--rm', '--gpus', 'all', 'nvidia/cuda:11.8-base-ubuntu20.04', 
                     'nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    gpu_names = result.stdout.strip().split('\n')
                    details = {
                        'docker_gpu_available': True,
                        'gpu_count': len(gpu_names),
                        'gpu_names': gpu_names
                    }
                    return self.test_result("GPU Availability", True, details)
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # No GPU found
            return self.test_result(
                "GPU Availability", 
                False, 
                {'error': 'No GPU detected. CPU-only mode.', 'impact': 'AI inference will be slower'}
            )
            
        except Exception as e:
            return self.test_result(
                "GPU Availability", 
                False, 
                {'error': str(e)}
            )

    async def test_api_endpoints(self) -> bool:
        """Test 6: API Endpoints and Health Checks"""
        self.log("🌐 Testing API Endpoints...", "INFO")
        
        try:
            base_urls = [
                'http://localhost:8000',
                'http://127.0.0.1:8000'
            ]
            
            endpoints_to_test = [
                '/health',
                '/api/v1/status',
                '/api/v1/strategies/list'
            ]
            
            test_results = []
            
            for base_url in base_urls:
                self.log(f"Testing endpoints at {base_url}...", "INFO")
                
                for endpoint in endpoints_to_test:
                    try:
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            timeout=5,
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        test_results.append({
                            'url': f"{base_url}{endpoint}",
                            'status_code': response.status_code,
                            'response_time_ms': response.elapsed.total_seconds() * 1000,
                            'success': response.status_code == 200,
                            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
                        })
                        
                        if response.status_code == 200:
                            self.log(f"✅ {endpoint} - OK ({response.elapsed.total_seconds()*1000:.1f}ms)", "SUCCESS")
                        else:
                            self.log(f"❌ {endpoint} - HTTP {response.status_code}", "WARNING")
                            
                    except requests.exceptions.RequestException as e:
                        test_results.append({
                            'url': f"{base_url}{endpoint}",
                            'success': False,
                            'error': str(e)
                        })
                        self.log(f"❌ {endpoint} - Connection Error: {str(e)}", "ERROR")
                
                # If we got successful responses from this base_url, break
                if any(result.get('success', False) for result in test_results[-len(endpoints_to_test):]):
                    break
            
            successful_tests = sum(1 for result in test_results if result.get('success', False))
            
            details = {
                'total_endpoints_tested': len(test_results),
                'successful_responses': successful_tests,
                'test_results': test_results
            }
            
            return self.test_result("API Endpoints", successful_tests > 0, details)
            
        except Exception as e:
            return self.test_result(
                "API Endpoints", 
                False, 
                {'error': str(e)}
            )

    async def test_database_connectivity(self) -> bool:
        """Test 7: Database Connectivity"""
        self.log("💾 Testing Database Connectivity...", "INFO")
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            db_url = self.config.DATABASE_URL
            if not db_url:
                return self.test_result(
                    "Database Connectivity", 
                    False, 
                    {'error': 'DATABASE_URL not configured'}
                )
            
            # Parse database URL
            parsed = urlparse(db_url)
            
            # Test connection
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            # Test table creation (if needed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_check (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                );
            """)
            
            # Insert test record
            cursor.execute(
                "INSERT INTO health_check (status) VALUES (%s)",
                (f"Production verification at {datetime.now()}",)
            )
            conn.commit()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM health_check;")
            record_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            details = {
                'connection': 'SUCCESS',
                'database_version': db_version,
                'test_table_records': record_count,
                'host': parsed.hostname,
                'database': parsed.path.lstrip('/')
            }
            
            return self.test_result("Database Connectivity", True, details)
            
        except Exception as e:
            return self.test_result(
                "Database Connectivity", 
                False, 
                {'error': str(e)}
            )

    async def test_kubernetes_deployment(self) -> bool:
        """Test 8: Kubernetes Deployment Status"""
        self.log("☸️  Testing Kubernetes Deployment...", "INFO")
        
        try:
            # Check if kubectl is available
            result = subprocess.run(
                ['kubectl', 'version', '--client', '--output=json'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                return self.test_result(
                    "Kubernetes Deployment", 
                    False, 
                    {'error': 'kubectl not available or not configured'}
                )
            
            # Check cluster connectivity
            result = subprocess.run(
                ['kubectl', 'cluster-info', '--request-timeout=10s'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                return self.test_result(
                    "Kubernetes Deployment", 
                    False, 
                    {'error': 'Cannot connect to Kubernetes cluster', 'output': result.stderr}
                )
            
            # Get pods in infinityai namespace
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', 'infinityai', '--output=json'],
                capture_output=True, text=True, check=False
            )
            
            pods_info = {'infinityai_namespace': 'not_found'}
            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                pods_info = {
                    'infinityai_namespace': 'found',
                    'total_pods': len(pods_data.get('items', [])),
                    'running_pods': len([p for p in pods_data.get('items', []) 
                                       if p.get('status', {}).get('phase') == 'Running']),
                    'pod_details': [
                        {
                            'name': p['metadata']['name'],
                            'status': p.get('status', {}).get('phase', 'Unknown'),
                            'ready': len([c for c in p.get('status', {}).get('containerStatuses', []) 
                                        if c.get('ready', False)])
                        }
                        for p in pods_data.get('items', [])
                    ]
                }
            
            # Check GPU nodes
            result = subprocess.run(
                ['kubectl', 'get', 'nodes', '-l', 'nvidia.com/gpu.present=true', '--output=json'],
                capture_output=True, text=True, check=False
            )
            
            gpu_nodes_info = {'gpu_nodes': 0}
            if result.returncode == 0:
                nodes_data = json.loads(result.stdout)
                gpu_nodes_info = {
                    'gpu_nodes': len(nodes_data.get('items', [])),
                    'node_details': [
                        {
                            'name': n['metadata']['name'],
                            'ready': any(c.get('type') == 'Ready' and c.get('status') == 'True' 
                                       for c in n.get('status', {}).get('conditions', []))
                        }
                        for n in nodes_data.get('items', [])
                    ]
                }
            
            details = {
                'kubectl_available': True,
                'cluster_accessible': True,
                **pods_info,
                **gpu_nodes_info
            }
            
            success = pods_info.get('running_pods', 0) > 0 or gpu_nodes_info.get('gpu_nodes', 0) > 0
            
            return self.test_result("Kubernetes Deployment", success, details)
            
        except Exception as e:
            return self.test_result(
                "Kubernetes Deployment", 
                False, 
                {'error': str(e)}
            )

    async def test_monitoring_stack(self) -> bool:
        """Test 9: Monitoring Stack (Prometheus, Grafana)"""
        self.log("📊 Testing Monitoring Stack...", "INFO")
        
        try:
            monitoring_endpoints = [
                ('Prometheus', 'http://localhost:9090/api/v1/query?query=up'),
                ('Grafana', 'http://localhost:3000/api/health'),
                ('Jaeger', 'http://localhost:16686/api/services')
            ]
            
            results = []
            
            for service, url in monitoring_endpoints:
                try:
                    response = requests.get(url, timeout=5)
                    success = response.status_code == 200
                    
                    results.append({
                        'service': service,
                        'url': url,
                        'status_code': response.status_code,
                        'success': success,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    })
                    
                    if success:
                        self.log(f"✅ {service} - Accessible", "SUCCESS")
                    else:
                        self.log(f"❌ {service} - HTTP {response.status_code}", "WARNING")
                        
                except requests.exceptions.RequestException as e:
                    results.append({
                        'service': service,
                        'url': url,
                        'success': False,
                        'error': str(e)
                    })
                    self.log(f"❌ {service} - Connection failed: {str(e)}", "WARNING")
            
            # Check kubectl port-forward for monitoring services
            kubectl_services = []
            try:
                result = subprocess.run(
                    ['kubectl', 'get', 'svc', '-n', 'monitoring', '--output=json'],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0:
                    services_data = json.loads(result.stdout)
                    kubectl_services = [
                        {
                            'name': s['metadata']['name'],
                            'type': s.get('spec', {}).get('type', 'Unknown'),
                            'ports': s.get('spec', {}).get('ports', [])
                        }
                        for s in services_data.get('items', [])
                    ]
            except:
                pass
            
            successful_connections = sum(1 for r in results if r.get('success', False))
            
            details = {
                'endpoint_tests': results,
                'successful_connections': successful_connections,
                'total_services_tested': len(results),
                'kubernetes_monitoring_services': kubectl_services
            }
            
            return self.test_result(
                "Monitoring Stack", 
                successful_connections > 0 or len(kubectl_services) > 0, 
                details
            )
            
        except Exception as e:
            return self.test_result(
                "Monitoring Stack", 
                False, 
                {'error': str(e)}
            )

    async def test_end_to_end_trading_flow(self) -> bool:
        """Test 10: End-to-End Trading Flow Simulation"""
        self.log("🎯 Testing End-to-End Trading Flow...", "INFO")
        
        try:
            if not self.data_integrator or not self.strategy:
                self.log("Initializing components for E2E test...", "INFO")
                self.data_integrator = DataAPIIntegrator()
                self.strategy = GiftNiftyMomentumAI()
            
            # Step 1: Fetch real market data
            self.log("Step 1: Fetching real market data from Dhan...", "INFO")
            symbol = "NIFTY"
            historical_data = await self.data_integrator.get_historical_data(
                'dhan', symbol, '1D', 5
            )
            
            if not historical_data:
                return self.test_result(
                    "End-to-End Trading Flow", 
                    False, 
                    {'error': 'Failed to fetch market data'}
                )
            
            latest_data = historical_data[0]
            current_price = latest_data.get('close', 0)
            
            # Step 2: Generate AI signals
            self.log("Step 2: Generating AI trading signals...", "INFO")
            market_data = {
                'symbol': symbol,
                'current_price': current_price,
                'volume': latest_data.get('volume', 0),
                'high': latest_data.get('high', 0),
                'low': latest_data.get('low', 0),
                'timestamp': datetime.now()
            }
            
            signals = await self.strategy.generate_signals(market_data)
            
            # Step 3: Risk management
            self.log("Step 3: Calculating risk metrics...", "INFO")
            portfolio_value = 25000  # As per strategy config
            risk_metrics = await self.strategy.calculate_risk_metrics(
                market_data, portfolio_value
            )
            
            # Step 4: Position sizing
            self.log("Step 4: Calculating position size...", "INFO")
            position_size = await self.strategy.calculate_position_size(
                current_price, portfolio_value, risk_metrics
            )
            
            # Step 5: Mock order placement (dry run)
            self.log("Step 5: Simulating order placement (dry run)...", "INFO")
            mock_order = {
                'symbol': symbol,
                'side': signals.get('action', 'HOLD'),
                'quantity': position_size,
                'price': current_price,
                'order_type': 'LIMIT',
                'timestamp': datetime.now().isoformat()
            }
            
            # Simulate order validation
            order_valid = all([
                signals.get('confidence', 0) > 0.6,
                position_size > 0,
                risk_metrics.get('max_loss_percent', 100) <= 8  # Max 8% loss
            ])
            
            details = {
                'market_data': {
                    'symbol': symbol,
                    'current_price': current_price,
                    'data_points_fetched': len(historical_data)
                },
                'ai_signals': signals,
                'risk_metrics': risk_metrics,
                'position_size': position_size,
                'mock_order': mock_order,
                'order_validation': {
                    'valid': order_valid,
                    'confidence_check': signals.get('confidence', 0) > 0.6,
                    'risk_check': risk_metrics.get('max_loss_percent', 100) <= 8
                },
                'flow_steps_completed': 5
            }
            
            success = all([
                len(historical_data) > 0,
                signals is not None,
                risk_metrics is not None,
                position_size > 0
            ])
            
            return self.test_result("End-to-End Trading Flow", success, details)
            
        except Exception as e:
            return self.test_result(
                "End-to-End Trading Flow", 
                False, 
                {'error': str(e)}
            )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        
        # Calculate summary statistics
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for test in self.results['tests'] if test['passed'])
        failed_tests = total_tests - passed_tests
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if pass_rate >= 90:
            overall_status = "EXCELLENT"
            status_emoji = "🎉"
        elif pass_rate >= 75:
            overall_status = "GOOD"
            status_emoji = "✅"
        elif pass_rate >= 50:
            overall_status = "PARTIAL"
            status_emoji = "⚠️"
        else:
            overall_status = "CRITICAL"
            status_emoji = "🚨"
        
        self.results['overall_status'] = overall_status
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate_percent': round(pass_rate, 1),
            'status_emoji': status_emoji
        }
        
        return self.results

    async def run_all_tests(self):
        """Run all verification tests"""
        
        self.log("🚀 Starting InfinityAI.Pro Production Verification", "INFO")
        self.log("=" * 60, "INFO")
        
        # List of all tests to run
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Docker Services", self.test_docker_services),
            ("Dhan API Connection", self.test_dhan_api_connection),
            ("AI Strategy", self.test_ai_strategy),
            ("GPU Availability", self.test_gpu_availability),
            ("API Endpoints", self.test_api_endpoints),
            ("Database Connectivity", self.test_database_connectivity),
            ("Kubernetes Deployment", self.test_kubernetes_deployment),
            ("Monitoring Stack", self.test_monitoring_stack),
            ("End-to-End Trading Flow", self.test_end_to_end_trading_flow)
        ]
        
        # Run each test
        for i, (test_name, test_func) in enumerate(tests, 1):
            self.log(f"\n[{i}/{len(tests)}] Running {test_name}...", "INFO")
            await test_func()
            time.sleep(1)  # Brief pause between tests
        
        # Generate final report
        self.log("\n" + "=" * 60, "INFO")
        self.log("🎯 Generating Verification Report...", "INFO")
        
        report = self.generate_report()
        
        # Display summary
        summary = report['summary']
        self.log(f"\n{summary['status_emoji']} VERIFICATION COMPLETE!", "SUCCESS")
        self.log(f"Overall Status: {report['overall_status']}", "SUCCESS")
        self.log(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['pass_rate_percent']}%)", "SUCCESS")
        
        # Save detailed report
        report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log(f"📄 Detailed report saved to: {report_file}", "INFO")
        
        # Display failed tests if any
        failed_tests = [test for test in report['tests'] if not test['passed']]
        if failed_tests:
            self.log(f"\n⚠️  FAILED TESTS ({len(failed_tests)}):", "WARNING")
            for test in failed_tests:
                self.log(f"  ❌ {test['test_name']}: {test.get('details', {}).get('error', 'Unknown error')}", "ERROR")
        
        return report

async def main():
    """Main verification function"""
    verifier = ProductionVerifier()
    report = await verifier.run_all_tests()
    
    # Exit with appropriate code
    if report['summary']['pass_rate_percent'] >= 75:
        return 0  # Success
    else:
        return 1  # Failure

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)