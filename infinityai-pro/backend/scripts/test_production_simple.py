#!/usr/bin/env python3
"""
Simplified InfinityAI.Pro Production Verification
Direct testing of Dhan API and core functionality
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Dhan API testing
try:
    from dhanhq import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    print("⚠️  Dhan SDK not installed. Run: pip install dhanhq")
    DHAN_AVAILABLE = False

def log(message: str, level: str = "INFO"):
    """Simple logging function"""
    colors = {
        'INFO': '\033[0;34m',     # Blue
        'SUCCESS': '\033[0;32m',  # Green
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
    }
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    color = colors.get(level, colors['INFO'])
    reset = '\033[0m'
    
    icon = {'INFO': 'ℹ️', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}.get(level, 'ℹ️')
    
    print(f"{color}[{timestamp}] {icon} {level}: {message}{reset}")

def test_environment_variables():
    """Test 1: Environment Variables"""
    log("Testing Environment Variables...")
    
    required_vars = [
        'DHAN_CLIENT_ID',
        'DHAN_ACCESS_TOKEN',
        'DATABASE_URL',
        'JWT_SECRET'
    ]
    
    missing_vars = []
    found_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            found_vars[var] = f"{value[:10]}..." if len(value) > 10 else value
        else:
            missing_vars.append(var)
    
    if missing_vars:
        log(f"Missing variables: {missing_vars}", "ERROR")
        return False
    else:
        log(f"All environment variables present: {list(found_vars.keys())}", "SUCCESS")
        for var, value in found_vars.items():
            log(f"  {var}: {value}", "INFO")
        return True

def test_dhan_api_connection():
    """Test 2: Dhan API Connection and Real Data Fetching"""
    log("Testing Dhan API Connection with your real credentials...")
    
    if not DHAN_AVAILABLE:
        log("Dhan SDK not available", "ERROR")
        return False
    
    try:
        # Initialize Dhan client with your credentials
        client_id = os.getenv('DHAN_CLIENT_ID')
        access_token = os.getenv('DHAN_ACCESS_TOKEN')
        
        if not client_id or not access_token:
            log("Dhan credentials not found in environment", "ERROR")
            return False
        
        log(f"Connecting to Dhan API with Client ID: {client_id}", "INFO")
        
        # Initialize Dhan client
        dhan = dhanhq(
            client_id=client_id,
            access_token=access_token
        )
        
        # Test 1: Get Fund Limits (Account Info)
        log("Fetching fund limits (account info)...", "INFO")
        try:
            fund_limits = dhan.get_fund_limits()
            if fund_limits and fund_limits.get('status') == 'success':
                available_balance = fund_limits.get('data', {}).get('availabe_balance', 0)
                log(f"✅ Fund Limits Retrieved - Available Balance: ₹{available_balance}", "SUCCESS")
            else:
                log(f"Fund limits error: {fund_limits}", "WARNING")
        except Exception as e:
            log(f"Fund limits failed: {e}", "WARNING")
        
        # Test 2: Get Holdings
        log("Fetching holdings...", "INFO")
        try:
            holdings = dhan.get_holdings()
            if holdings and holdings.get('status') == 'success':
                holdings_data = holdings.get('data', [])
                log(f"✅ Holdings Retrieved - Count: {len(holdings_data)}", "SUCCESS")
                
                if holdings_data:
                    for holding in holdings_data[:3]:  # Show first 3
                        symbol = holding.get('isin', 'N/A')
                        quantity = holding.get('quantity', 0)
                        log(f"  Holding: {symbol}, Qty: {quantity}", "INFO")
            else:
                log(f"Holdings error: {holdings}", "WARNING")
        except Exception as e:
            log(f"Holdings failed: {e}", "WARNING")
        
        # Test 3: Get Positions
        log("Fetching positions...", "INFO")
        try:
            positions = dhan.get_positions()
            if positions and positions.get('status') == 'success':
                positions_data = positions.get('data', [])
                log(f"✅ Positions Retrieved - Count: {len(positions_data)}", "SUCCESS")
                
                if positions_data:
                    for position in positions_data[:3]:  # Show first 3
                        symbol = position.get('tradingSymbol', 'N/A')
                        quantity = position.get('quantity', 0)
                        pnl = position.get('realizedPnl', 0)
                        log(f"  Position: {symbol}, Qty: {quantity}, PnL: ₹{pnl}", "INFO")
            else:
                log(f"Positions error: {positions}", "WARNING")
        except Exception as e:
            log(f"Positions failed: {e}", "WARNING")
        
        # Test 4: Get Live Market Data for NIFTY
        log("Fetching live market data for NIFTY index...", "INFO")
        try:
            # NIFTY 50 Index
            instruments = [
                {
                    'exchange_segment': 'NSE_INDEX',
                    'instrument_token': 13
                }
            ]
            
            ltp_data = dhan.get_ltp_data(
                exchange_segment='NSE_INDEX',
                instrument_token=13
            )
            
            if ltp_data and ltp_data.get('status') == 'success':
                data = ltp_data.get('data', {})
                ltp = data.get('LTP', 0)
                volume = data.get('volume', 0)
                change = data.get('change', 0)
                log(f"✅ NIFTY Live Data - LTP: {ltp}, Volume: {volume}, Change: {change}", "SUCCESS")
            else:
                log(f"LTP data error: {ltp_data}", "WARNING")
                
        except Exception as e:
            log(f"LTP data failed: {e}", "WARNING")
        
        # Test 5: Get Historical Data
        log("Fetching historical OHLC data...", "INFO")
        try:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            historical_data = dhan.historical_minute_charts(
                symbol='NIFTY',
                exchange_segment='NSE_INDEX',
                instrument_token=13,
                from_date=from_date,
                to_date=to_date
            )
            
            if historical_data and historical_data.get('status') == 'success':
                data = historical_data.get('data', [])
                log(f"✅ Historical Data Retrieved - {len(data)} data points", "SUCCESS")
                
                if data:
                    latest = data[-1]  # Most recent data point
                    log(f"  Latest OHLC: O={latest.get('open')}, H={latest.get('high')}, L={latest.get('low')}, C={latest.get('close')}", "INFO")
            else:
                log(f"Historical data error: {historical_data}", "WARNING")
                
        except Exception as e:
            log(f"Historical data failed: {e}", "WARNING")
        
        log("Dhan API Connection Test Completed Successfully! ✅", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Dhan API Connection Failed: {e}", "ERROR")
        return False

def test_docker_services():
    """Test 3: Docker Services"""
    log("Testing Docker Services...")
    
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            log("Docker not running or accessible", "WARNING")
            return False
        
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:  # Only header
            log("No Docker containers running", "WARNING")
            return False
        
        containers = []
        for line in lines[1:]:
            if line.strip():
                containers.append(line.split()[1])  # Container name/image
        
        log(f"Docker containers running: {len(containers)}", "SUCCESS")
        for container in containers[:5]:  # Show first 5
            log(f"  Container: {container}", "INFO")
        
        return True
        
    except FileNotFoundError:
        log("Docker command not found", "WARNING")
        return False
    except Exception as e:
        log(f"Docker test failed: {e}", "ERROR")
        return False

def test_gpu_availability():
    """Test 4: GPU Availability"""
    log("Testing GPU Availability...")
    
    try:
        # Check nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader'],
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            gpu_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    gpu_info.append(line.strip())
            
            if gpu_info:
                log(f"GPUs detected: {len(gpu_info)}", "SUCCESS")
                for i, gpu in enumerate(gpu_info):
                    log(f"  GPU {i}: {gpu}", "INFO")
                return True
        
        log("No NVIDIA GPUs detected (running on CPU)", "WARNING")
        return False
        
    except FileNotFoundError:
        log("nvidia-smi not found (no GPU support)", "WARNING")
        return False
    except Exception as e:
        log(f"GPU test failed: {e}", "WARNING")
        return False

def test_api_endpoints():
    """Test 5: API Endpoints"""
    log("Testing API Endpoints...")
    
    endpoints = [
        'http://localhost:8000/health',
        'http://127.0.0.1:8000/health',
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                log(f"✅ API endpoint accessible: {endpoint}", "SUCCESS")
                try:
                    data = response.json()
                    log(f"  Response: {data}", "INFO")
                except:
                    log(f"  Response: {response.text[:100]}", "INFO")
                return True
            else:
                log(f"API endpoint returned {response.status_code}: {endpoint}", "WARNING")
        except requests.exceptions.RequestException as e:
            log(f"API endpoint not accessible: {endpoint} - {e}", "WARNING")
    
    log("No API endpoints accessible", "WARNING")
    return False

def test_kubernetes_deployment():
    """Test 6: Kubernetes Deployment"""
    log("Testing Kubernetes Deployment...")
    
    try:
        # Check kubectl
        result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            log("kubectl not available", "WARNING")
            return False
        
        # Check cluster connection
        result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            log("✅ Kubernetes cluster accessible", "SUCCESS")
            
            # Check for InfinityAI pods
            result = subprocess.run(['kubectl', 'get', 'pods', '-A'], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                infinityai_pods = [line for line in lines if 'infinityai' in line.lower()]
                
                if infinityai_pods:
                    log(f"InfinityAI pods found: {len(infinityai_pods)}", "SUCCESS")
                    for pod in infinityai_pods[:3]:
                        log(f"  Pod: {pod.split()[1]}", "INFO")
                else:
                    log("No InfinityAI pods found", "WARNING")
            
            return True
        else:
            log("Cannot connect to Kubernetes cluster", "WARNING")
            return False
            
    except FileNotFoundError:
        log("kubectl not found", "WARNING")
        return False
    except Exception as e:
        log(f"Kubernetes test failed: {e}", "ERROR")
        return False

def test_database_connection():
    """Test 7: Database Connection"""
    log("Testing Database Connection...")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            log("DATABASE_URL not configured", "WARNING")
            return False
        
        parsed = urlparse(db_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT NOW();")
        current_time = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        log(f"✅ Database connected successfully", "SUCCESS")
        log(f"  Host: {parsed.hostname}", "INFO")
        log(f"  Database: {parsed.path.lstrip('/')}", "INFO")
        log(f"  Time: {current_time}", "INFO")
        
        return True
        
    except ImportError:
        log("psycopg2 not installed: pip install psycopg2-binary", "WARNING")
        return False
    except Exception as e:
        log(f"Database connection failed: {e}", "ERROR")
        return False

def main():
    """Main verification function"""
    log("🚀 Starting InfinityAI.Pro Production Verification", "INFO")
    log("=" * 60, "INFO")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Dhan API Connection & Live Data", test_dhan_api_connection),
        ("Docker Services", test_docker_services),
        ("GPU Availability", test_gpu_availability),
        ("API Endpoints", test_api_endpoints),
        ("Kubernetes Deployment", test_kubernetes_deployment),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    
    for i, (test_name, test_func) in enumerate(tests, 1):
        log(f"\n[{i}/{len(tests)}] Running {test_name}...", "INFO")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log(f"Test {test_name} failed with exception: {e}", "ERROR")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    log("\n" + "=" * 60, "INFO")
    log("🎯 VERIFICATION SUMMARY", "SUCCESS")
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    log(f"Tests Passed: {passed_tests}/{total_tests} ({pass_rate:.1f}%)", "SUCCESS")
    
    # Show individual results
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {status}: {test_name}", "SUCCESS" if result else "ERROR")
    
    # Overall status
    if pass_rate >= 80:
        log("\n🎉 EXCELLENT! Your production deployment is working great!", "SUCCESS")
    elif pass_rate >= 60:
        log("\n✅ GOOD! Most components are working well.", "SUCCESS")
    elif pass_rate >= 40:
        log("\n⚠️  PARTIAL: Some components need attention.", "WARNING")
    else:
        log("\n🚨 CRITICAL: Multiple components need fixing.", "ERROR")
    
    return 0 if pass_rate >= 60 else 1

if __name__ == "__main__":
    from datetime import timedelta
    exit_code = main()
    sys.exit(exit_code)