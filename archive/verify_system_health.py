#!/usr/bin/env python3
"""
InfinityAI.Pro - Full System Verification with Emotional Ritual Logging
A comprehensive health check system that verifies all engines, webhooks, and data flows
while maintaining emotional awareness and philosophical alignment.
"""

import argparse
import asyncio
import aiohttp
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import traceback

# Emotional and philosophical constants
RITUAL_MESSAGES = {
    "initiation": "🧘 System verification initiated. This is a moment of clarity and alignment.",
    "engine_check": "⚡ Checking engine vitality. Each service represents a facet of our digital consciousness.",
    "webhook_verify": "🔗 Verifying connection pathways. Communication channels are the nervous system of our platform.",
    "market_data": "📊 Assessing market data flow. Information is the lifeblood of informed decision-making.",
    "auth_check": "🔐 Validating authentication integrity. Trust is the foundation of all financial operations.",
    "dashboard_sync": "🎛️ Synchronizing dashboard state. Transparency creates confidence and clarity.",
    "emotional_journal": "💫 Checking emotional journal. Self-awareness guides technological evolution.",
    "success": "✅ All systems verified. Emotional and architectural integrity confirmed. Celebrate this milestone.",
    "partial_success": "⚠️ Partial verification complete. Some systems need attention. Growth comes through addressing challenges.",
    "failure": "⚠️ Verification failed. Pause, reflect, and begin troubleshooting with emotional awareness."
}

@dataclass
class VerificationResult:
    component: str
    status: str  # "success", "warning", "failure"
    response_time_ms: int
    message: str
    details: Optional[Dict] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

@dataclass
class SystemHealthReport:
    timestamp: str
    total_components: int
    successful: int
    warnings: int
    failures: int
    overall_status: str
    results: List[VerificationResult]
    emotional_state: str
    ritual_completion: bool
    performance_metrics: Dict

class EmotionalLogger:
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("InfinityAI.SystemHealth")
    
    def ritual_log(self, phase: str, message: str = None):
        ritual_msg = message or RITUAL_MESSAGES.get(phase, f"🔮 {phase.title()} phase initiated")
        self.logger.info(f"🎋 RITUAL: {ritual_msg}")
        print(f"\n🎋 {ritual_msg}")
    
    def emotional_entry(self, emotion: str, context: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"💫 EMOTIONAL JOURNAL [{timestamp}]: {emotion} - {context}"
        self.logger.info(entry)
        print(entry)

class SystemVerifier:
    def __init__(self, logger: EmotionalLogger):
        self.logger = logger
        self.session = None
        
        # Engine configurations
        self.engines = {
            "EngineA": "https://engine-a-market-data-prod-573866363639.us-central1.run.app",
            "EngineB": "http://localhost:8081",  # Placeholder for Engine B
            "EngineC": "http://localhost:8082"   # Placeholder for Engine C
        }
        
        # Webhook configurations
        self.webhooks = {
            "telegram": "https://api.telegram.org/bot",  # Will need bot token
            "dhan": "https://api.dhan.co/v2/webhook",
            "zerodha": "https://api.kite.trade/webhook"
        }
        
        # Market data endpoints
        self.market_endpoints = {
            "NSE": "https://www.nseindia.com/api/market-data-pre-open?key=ALL",
            "BSE": "https://api.bseindia.com/BseIndiaAPI/api/GetMktData/w"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_endpoint(self, name: str, url: str, timeout: int = 10) -> VerificationResult:
        start_time = time.time()
        try:
            async with self.session.get(url) as response:
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return VerificationResult(
                            component=name,
                            status="success",
                            response_time_ms=response_time,
                            message=f"Endpoint responsive - {response.status}",
                            details={"status_code": response.status, "has_data": bool(data)}
                        )
                    except:
                        return VerificationResult(
                            component=name,
                            status="success",
                            response_time_ms=response_time,
                            message=f"Endpoint responsive (non-JSON) - {response.status}",
                            details={"status_code": response.status}
                        )
                else:
                    return VerificationResult(
                        component=name,
                        status="warning",
                        response_time_ms=response_time,
                        message=f"Unexpected status code: {response.status}",
                        details={"status_code": response.status}
                    )
                    
        except asyncio.TimeoutError:
            response_time = int((time.time() - start_time) * 1000)
            return VerificationResult(
                component=name,
                status="failure",
                response_time_ms=response_time,
                message="Request timeout",
                details={"error": "timeout"}
            )
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return VerificationResult(
                component=name,
                status="failure",
                response_time_ms=response_time,
                message=f"Connection failed: {str(e)}",
                details={"error": str(e)}
            )

    async def verify_engines(self, engine_list: List[str]) -> List[VerificationResult]:
        self.logger.ritual_log("engine_check")
        results = []
        
        for engine in engine_list:
            if engine in self.engines:
                self.logger.logger.info(f"🔍 Checking {engine}...")
                # Check health endpoint
                health_url = f"{self.engines[engine]}/health"
                result = await self.check_endpoint(f"{engine}_health", health_url)
                results.append(result)
                
                # Check main endpoint
                main_result = await self.check_endpoint(f"{engine}_main", self.engines[engine])
                results.append(main_result)
                
                # Emotional logging
                if result.status == "success":
                    self.logger.emotional_entry("Confidence", f"{engine} is responding well - system harmony maintained")
                else:
                    self.logger.emotional_entry("Concern", f"{engine} showing issues - attention and care needed")
            else:
                results.append(VerificationResult(
                    component=f"{engine}_config",
                    status="failure",
                    response_time_ms=0,
                    message=f"Engine {engine} not configured"
                ))
        
        return results

    async def verify_webhooks(self, webhook_list: List[str]) -> List[VerificationResult]:
        self.logger.ritual_log("webhook_verify")
        results = []
        
        for webhook in webhook_list:
            self.logger.logger.info(f"🔗 Checking {webhook} webhook...")
            
            if webhook == "telegram":
                # For Telegram, we'd need to check bot API
                results.append(VerificationResult(
                    component="telegram_webhook",
                    status="warning",
                    response_time_ms=0,
                    message="Telegram webhook verification requires bot token configuration"
                ))
            elif webhook in self.webhooks:
                result = await self.check_endpoint(f"{webhook}_webhook", self.webhooks[webhook])
                results.append(result)
            else:
                results.append(VerificationResult(
                    component=f"{webhook}_webhook",
                    status="failure",
                    response_time_ms=0,
                    message=f"Webhook {webhook} not configured"
                ))
        
        return results

    async def verify_market_data(self, exchanges: List[str]) -> List[VerificationResult]:
        self.logger.ritual_log("market_data")
        results = []
        
        for exchange in exchanges:
            if exchange in self.market_endpoints:
                self.logger.logger.info(f"📊 Checking {exchange} market data...")
                result = await self.check_endpoint(f"{exchange}_market_data", self.market_endpoints[exchange])
                results.append(result)
                
                if result.status == "success":
                    self.logger.emotional_entry("Flow", f"{exchange} data flowing - connected to market pulse")
                else:
                    self.logger.emotional_entry("Disconnection", f"{exchange} data issues - market insight compromised")
        
        return results

    def verify_emotional_journal(self) -> VerificationResult:
        self.logger.ritual_log("emotional_journal")
        
        # Check if emotional journal is working by writing an entry
        try:
            self.logger.emotional_entry("System_Check", "Emotional journal verification - consciousness stream active")
            
            # Verify log file exists and is writable
            if self.logger.log_file.exists():
                return VerificationResult(
                    component="emotional_journal",
                    status="success",
                    response_time_ms=0,
                    message="Emotional journal active and logging",
                    details={"log_file": str(self.logger.log_file)}
                )
            else:
                return VerificationResult(
                    component="emotional_journal",
                    status="failure",
                    response_time_ms=0,
                    message="Emotional journal log file not accessible"
                )
        except Exception as e:
            return VerificationResult(
                component="emotional_journal",
                status="failure",
                response_time_ms=0,
                message=f"Emotional journal error: {str(e)}"
            )

    def verify_auth_system(self) -> VerificationResult:
        self.logger.ritual_log("auth_check")
        
        # Check for environment variables or config files
        auth_checks = {
            "dhan_token": os.getenv("DHAN_ACCESS_TOKEN") is not None,
            "vertex_key": os.getenv("GCP_GEMINI_API_KEY") is not None,
            "hf_token": os.getenv("HF_API_TOKEN") is not None
        }
        
        success_count = sum(auth_checks.values())
        total_checks = len(auth_checks)
        
        if success_count == total_checks:
            self.logger.emotional_entry("Trust", "All authentication systems verified - foundation is solid")
            return VerificationResult(
                component="authentication",
                status="success",
                response_time_ms=0,
                message="All authentication credentials configured",
                details=auth_checks
            )
        elif success_count > 0:
            self.logger.emotional_entry("Partial_Trust", "Some auth systems configured - gaps need attention")
            return VerificationResult(
                component="authentication",
                status="warning",
                response_time_ms=0,
                message=f"{success_count}/{total_checks} authentication systems configured",
                details=auth_checks
            )
        else:
            self.logger.emotional_entry("Vulnerability", "Authentication systems not configured - security at risk")
            return VerificationResult(
                component="authentication",
                status="failure",
                response_time_ms=0,
                message="No authentication credentials found",
                details=auth_checks
            )

async def main():
    parser = argparse.ArgumentParser(description="InfinityAI Full System Verification")
    parser.add_argument("--check-engines", default="EngineA", help="Comma-separated list of engines to check")
    parser.add_argument("--verify-webhooks", default="dhan,telegram", help="Comma-separated list of webhooks to verify")
    parser.add_argument("--dashboard-sync", default="true", help="Check dashboard synchronization")
    parser.add_argument("--emotional-journal", default="true", help="Verify emotional journal system")
    parser.add_argument("--market-data-flow", default="NSE,BSE", help="Check market data flow")
    parser.add_argument("--auth-check", default="true", help="Verify authentication systems")
    parser.add_argument("--log-output", default="logs/health_check.log", help="Log file path")
    parser.add_argument("--ritual-alert", help="Custom ritual initiation message")
    parser.add_argument("--success-alert", help="Custom success message")
    parser.add_argument("--failure-alert", help="Custom failure message")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--retry", type=int, default=3, help="Number of retries")
    parser.add_argument("--notify", default="false", help="Send notifications")
    
    args = parser.parse_args()
    
    # Initialize emotional logger
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = args.log_output.replace("$(date +%Y%m%d_%H%M%S)", timestamp)
    logger = EmotionalLogger(log_file)
    
    # Ritual initiation
    initiation_msg = args.ritual_alert or RITUAL_MESSAGES["initiation"]
    logger.ritual_log("initiation", initiation_msg)
    
    start_time = time.time()
    all_results = []
    
    async with SystemVerifier(logger) as verifier:
        try:
            # Check engines
            if args.check_engines:
                engines = [e.strip() for e in args.check_engines.split(",")]
                engine_results = await verifier.verify_engines(engines)
                all_results.extend(engine_results)
            
            # Verify webhooks
            if args.verify_webhooks:
                webhooks = [w.strip() for w in args.verify_webhooks.split(",")]
                webhook_results = await verifier.verify_webhooks(webhooks)
                all_results.extend(webhook_results)
            
            # Check market data
            if args.market_data_flow:
                exchanges = [e.strip() for e in args.market_data_flow.split(",")]
                market_results = await verifier.verify_market_data(exchanges)
                all_results.extend(market_results)
            
            # Verify emotional journal
            if args.emotional_journal.lower() == "true":
                journal_result = verifier.verify_emotional_journal()
                all_results.append(journal_result)
            
            # Check authentication
            if args.auth_check.lower() == "true":
                auth_result = verifier.verify_auth_system()
                all_results.append(auth_result)
            
        except Exception as e:
            logger.logger.error(f"Verification error: {str(e)}")
            logger.emotional_entry("System_Error", f"Unexpected error during verification: {str(e)}")
            all_results.append(VerificationResult(
                component="system_verification",
                status="failure",
                response_time_ms=0,
                message=f"System verification error: {str(e)}"
            ))
    
    # Calculate results
    total_time = int((time.time() - start_time) * 1000)
    successful = len([r for r in all_results if r.status == "success"])
    warnings = len([r for r in all_results if r.status == "warning"])
    failures = len([r for r in all_results if r.status == "failure"])
    total_components = len(all_results)
    
    # Determine overall status
    if failures == 0 and warnings == 0:
        overall_status = "fully_operational"
        emotional_state = "Harmony"
        final_msg = args.success_alert or RITUAL_MESSAGES["success"]
    elif failures == 0:
        overall_status = "mostly_operational"
        emotional_state = "Cautious_Optimism"
        final_msg = args.success_alert or RITUAL_MESSAGES["partial_success"]
    else:
        overall_status = "needs_attention"
        emotional_state = "Concerned_Focus"
        final_msg = args.failure_alert or RITUAL_MESSAGES["failure"]
    
    # Performance metrics
    response_times = [r.response_time_ms for r in all_results if r.response_time_ms > 0]
    performance_metrics = {
        "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
        "max_response_time_ms": max(response_times) if response_times else 0,
        "min_response_time_ms": min(response_times) if response_times else 0,
        "total_verification_time_ms": total_time
    }
    
    # Create final report
    report = SystemHealthReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_components=total_components,
        successful=successful,
        warnings=warnings,
        failures=failures,
        overall_status=overall_status,
        results=all_results,
        emotional_state=emotional_state,
        ritual_completion=True,
        performance_metrics=performance_metrics
    )
    
    # Final ritual message
    logger.ritual_log("completion", final_msg)
    logger.emotional_entry(emotional_state, f"System verification complete - {successful}/{total_components} components healthy")
    
    # Print summary
    print("\n" + "="*80)
    print("🏆 INFINITYAI SYSTEM HEALTH REPORT")
    print("="*80)
    print(f"⏱️  Total Time: {total_time}ms")
    print(f"📊 Components Checked: {total_components}")
    print(f"✅ Successful: {successful}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"❌ Failures: {failures}")
    print(f"🎯 Overall Status: {overall_status.upper()}")
    print(f"💫 Emotional State: {emotional_state}")
    print(f"📈 Average Response Time: {performance_metrics['avg_response_time_ms']:.2f}ms")
    
    print("\n🔍 Component Details:")
    for result in all_results:
        status_icon = {"success": "✅", "warning": "⚠️", "failure": "❌"}[result.status]
        print(f"  {status_icon} {result.component}: {result.message} ({result.response_time_ms}ms)")
    
    # Save detailed report
    report_file = f"system_health_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(asdict(report), f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved: {report_file}")
    print(f"📝 Logs saved: {log_file}")
    
    # Exit with appropriate code
    sys.exit(0 if failures == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())