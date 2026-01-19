#!/usr/bin/env python3
"""
24-Hour Continuous Monitoring Script
Monitors market-data-ingestion and related services every 5 minutes
Logs results to file and cloud
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('24hour_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "galvanic-pulsar-482815-h0"
REGION = "us-central1"
FUNCTION_NAME = "market-data-ingestion"
SCHEDULER_NAME = "market-data-publisher"
MONITORING_DURATION = 24 * 60 * 60  # 24 hours in seconds
CHECK_INTERVAL = 5 * 60  # Check every 5 minutes in seconds

# Test URLs
FUNCTION_URL = "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/market-data-ingestion"
ENGINE_C_HEALTH = "https://engine-c-3acobgd3qa-uc.a.run.app/api/health"
ENGINE_C_STATUS = "https://engine-c-3acobgd3qa-uc.a.run.app/api/system/status"

class MonitoringMetrics:
    """Track monitoring metrics"""
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks_performed = 0
        self.errors = []
        self.errors_404 = 0
        self.errors_500 = 0
        self.errors_timeout = 0
        self.errors_other = 0
        self.latencies = []
        self.scheduler_executions = []
        self.engine_c_health_checks = []
        self.pub_sub_message_counts = []
    
    def record_error(self, error_type: str, message: str):
        """Record an error"""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": message
        })
        
        if "404" in str(message):
            self.errors_404 += 1
        elif "500" in str(message):
            self.errors_500 += 1
        elif "timeout" in str(message).lower():
            self.errors_timeout += 1
        else:
            self.errors_other += 1
    
    def record_latency(self, latency_ms: float):
        """Record function latency"""
        self.latencies.append(latency_ms)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        p99_latency = sorted(self.latencies)[int(len(self.latencies) * 0.99)] if self.latencies else 0
        error_rate = (len(self.errors) / self.checks_performed * 100) if self.checks_performed > 0 else 0
        
        return {
            "elapsed_seconds": elapsed,
            "checks_performed": self.checks_performed,
            "total_errors": len(self.errors),
            "error_rate_percent": error_rate,
            "errors_404": self.errors_404,
            "errors_500": self.errors_500,
            "errors_timeout": self.errors_timeout,
            "errors_other": self.errors_other,
            "avg_latency_ms": avg_latency,
            "p99_latency_ms": p99_latency,
            "scheduler_executions": len(self.scheduler_executions),
            "pub_sub_messages": sum(self.pub_sub_message_counts) if self.pub_sub_message_counts else 0,
            "engine_c_health_ok": sum(1 for h in self.engine_c_health_checks if h.get("ok"))
        }

def run_gcloud_command(command: List[str]) -> Dict[str, Any]:
    """Run a gcloud command and return result"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_function_health() -> tuple[bool, float, str]:
    """Test market-data-ingestion function"""
    import requests
    
    start = time.time()
    try:
        response = requests.post(
            FUNCTION_URL,
            json={},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            return True, latency, f"Success: {data.get('message', 'OK')}"
        else:
            return False, latency, f"HTTP {response.status_code}"
    except requests.Timeout:
        latency = (time.time() - start) * 1000
        return False, latency, "Timeout"
    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, latency, str(e)

def test_engine_c_health() -> Dict[str, Any]:
    """Test Engine-C health endpoint"""
    import requests
    
    try:
        response = requests.get(ENGINE_C_HEALTH, timeout=5)
        if response.status_code == 200:
            return {
                "ok": True,
                "status": response.json().get("status"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"ok": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def test_engine_c_status() -> Dict[str, Any]:
    """Test Engine-C system status endpoint (the fixed endpoint)"""
    import requests
    
    try:
        response = requests.get(ENGINE_C_STATUS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "ok": True,
                "status": data.get("status"),
                "trading_mode": data.get("trading_mode"),
                "market_hours": data.get("market_hours"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"ok": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_scheduler_status() -> Dict[str, Any]:
    """Check Cloud Scheduler job status"""
    command = [
        "gcloud", "scheduler", "jobs", "describe", SCHEDULER_NAME,
        "--location", REGION,
        "--project", PROJECT_ID,
        "--format", "json"
    ]
    result = run_gcloud_command(command)
    
    if result["success"]:
        try:
            data = json.loads(result["stdout"])
            return {
                "ok": data.get("state") == "ENABLED",
                "state": data.get("state"),
                "last_execution_time": data.get("lastExecutionTime"),
                "next_execution_time": data.get("nextExecutionTime")
            }
        except:
            return {"ok": False, "error": "Failed to parse scheduler status"}
    else:
        return {"ok": False, "error": result.get("stderr")}

def check_function_errors() -> Dict[str, Any]:
    """Check for errors in function logs"""
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    
    command = [
        "gcloud", "logging", "read",
        f"resource.type=cloud_run_revision AND resource.labels.service_name={FUNCTION_NAME} AND severity>=ERROR AND timestamp>='{one_hour_ago}'",
        "--limit", "100",
        "--format", "json",
        "--project", PROJECT_ID
    ]
    
    result = run_gcloud_command(command)
    
    if result["success"]:
        try:
            logs = json.loads(result["stdout"] or "[]")
            error_count = len(logs)
            error_messages = [log.get("jsonPayload", {}).get("message", "") for log in logs[:5]]
            
            return {
                "error_count": error_count,
                "latest_errors": error_messages,
                "status": "OK" if error_count == 0 else "ERRORS_FOUND"
            }
        except:
            return {"error_count": -1, "status": "PARSE_ERROR"}
    else:
        return {"error_count": -1, "status": "QUERY_ERROR", "stderr": result.get("stderr")}

def perform_check(metrics: MonitoringMetrics) -> Dict[str, Any]:
    """Perform one complete health check"""
    check_result = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check 1: Function health
    try:
        success, latency, message = test_function_health()
        check_result["checks"]["function_health"] = {
            "success": success,
            "latency_ms": latency,
            "message": message
        }
        metrics.record_latency(latency)
        if not success:
            metrics.record_error("function_health", message)
    except Exception as e:
        check_result["checks"]["function_health"] = {"error": str(e)}
        metrics.record_error("function_health", str(e))
    
    # Check 2: Engine-C health
    try:
        engine_health = test_engine_c_health()
        check_result["checks"]["engine_c_health"] = engine_health
        if engine_health.get("ok"):
            metrics.engine_c_health_checks.append(engine_health)
    except Exception as e:
        check_result["checks"]["engine_c_health"] = {"error": str(e)}
    
    # Check 3: Engine-C status (the fixed endpoint)
    try:
        engine_status = test_engine_c_status()
        check_result["checks"]["engine_c_status"] = engine_status
    except Exception as e:
        check_result["checks"]["engine_c_status"] = {"error": str(e)}
    
    # Check 4: Scheduler status
    try:
        scheduler_status = check_scheduler_status()
        check_result["checks"]["scheduler"] = scheduler_status
        if scheduler_status.get("ok"):
            metrics.scheduler_executions.append(scheduler_status)
    except Exception as e:
        check_result["checks"]["scheduler"] = {"error": str(e)}
    
    # Check 5: Function errors in logs
    try:
        errors_check = check_function_errors()
        check_result["checks"]["function_errors"] = errors_check
        if errors_check.get("error_count", 0) > 0:
            metrics.record_error("log_errors", f"{errors_check.get('error_count')} errors in logs")
    except Exception as e:
        check_result["checks"]["function_errors"] = {"error": str(e)}
    
    metrics.checks_performed += 1
    return check_result

def run_continuous_monitoring(duration_seconds: int = 86400):
    """Run continuous monitoring for specified duration"""
    metrics = MonitoringMetrics()
    start_time = time.time()
    check_count = 0
    
    logger.info("=" * 80)
    logger.info("STARTING 24-HOUR CONTINUOUS MONITORING")
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Function: {FUNCTION_NAME}")
    logger.info(f"Check Interval: Every {CHECK_INTERVAL} seconds")
    logger.info(f"Duration: {duration_seconds} seconds (~{duration_seconds // 3600} hours)")
    logger.info("=" * 80)
    
    while (time.time() - start_time) < duration_seconds:
        try:
            check_result = perform_check(metrics)
            check_count += 1
            
            # Log check result
            logger.info(f"\n[CHECK #{check_count}] {check_result['timestamp']}")
            logger.info(f"Function Health: {check_result['checks'].get('function_health', {}).get('message', 'N/A')}")
            logger.info(f"Engine-C Health: {check_result['checks'].get('engine_c_health', {}).get('status', 'N/A')}")
            logger.info(f"Scheduler: {check_result['checks'].get('scheduler', {}).get('state', 'N/A')}")
            logger.info(f"Function Errors (1hr): {check_result['checks'].get('function_errors', {}).get('error_count', 'N/A')}")
            
            # Log metrics summary every 6 checks (30 minutes)
            if check_count % 6 == 0:
                summary = metrics.get_summary()
                logger.info(f"\n=== 30-MINUTE SUMMARY (Check #{check_count}) ===")
                logger.info(f"Total Errors: {summary['total_errors']} (Error Rate: {summary['error_rate_percent']:.2f}%)")
                logger.info(f"Avg Latency: {summary['avg_latency_ms']:.0f}ms | P99: {summary['p99_latency_ms']:.0f}ms")
                logger.info(f"404 Errors: {summary['errors_404']} | 500 Errors: {summary['errors_500']} | Timeouts: {summary['errors_timeout']}")
                logger.info(f"Scheduler Executions: {summary['scheduler_executions']} | Engine-C OK: {summary['engine_c_health_ok']}/6")
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Check failed with error: {e}")
            time.sleep(CHECK_INTERVAL)
    
    # Final summary
    final_summary = metrics.get_summary()
    logger.info(f"\n" + "=" * 80)
    logger.info("24-HOUR MONITORING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total Duration: {final_summary['elapsed_seconds']:.0f} seconds")
    logger.info(f"Total Checks: {final_summary['checks_performed']}")
    logger.info(f"Total Errors: {final_summary['total_errors']}")
    logger.info(f"Error Rate: {final_summary['error_rate_percent']:.2f}%")
    logger.info(f"Avg Latency: {final_summary['avg_latency_ms']:.0f}ms")
    logger.info(f"P99 Latency: {final_summary['p99_latency_ms']:.0f}ms")
    logger.info(f"Scheduler Executions: {final_summary['scheduler_executions']}")
    logger.info(f"Engine-C Health OK: {final_summary['engine_c_health_ok']}/{final_summary['checks_performed']}")
    
    # Write final report
    with open('24hour_monitoring_report.json', 'w') as f:
        json.dump({
            "summary": final_summary,
            "errors": metrics.errors[:100]  # Last 100 errors
        }, f, indent=2)
    
    logger.info(f"\nReport written to: 24hour_monitoring_report.json")

if __name__ == "__main__":
    # Install required dependencies if not present
    try:
        import requests
    except ImportError:
        logger.warning("Installing requests library...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    
    # Run monitoring for 24 hours (or custom duration)
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 86400
    run_continuous_monitoring(duration)
