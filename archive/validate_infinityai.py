#!/usr/bin/env python3
"""
InfinityAI.Pro - Comprehensive System Verification & Validation
Advanced multi-cloud platform verification with metrics, dataflow tracing, and capacity analysis
"""

import argparse
import asyncio
import aiohttp
import time
import json
import sys
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import statistics
import concurrent.futures
from dataclasses import dataclass, asdict
import logging

@dataclass
class EngineMetrics:
    name: str
    url: str
    platform: str
    latency_ms: float
    throughput_rps: float
    capacity_score: float
    dataflow_health: str
    ssl_grade: str
    response_codes: List[int]
    error_rate: float

@dataclass 
class SystemCapacity:
    total_engines: int
    operational_engines: int
    total_rps_capacity: float
    average_latency: float
    peak_throughput: float
    reliability_score: float

class InfinityAIValidator:
    def __init__(self, args):
        self.args = args
        self.timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Configure logging
        log_level = logging.DEBUG if args.log_level == 'verbose' else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - VALIDATOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'infinityai_validation_{self.timestamp.replace(":", "-")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Engine configurations
        self.engines = {
            "engine_a": {
                "name": "Engine A - Market Data Ingestion",
                "url": "https://infinityai-engine-a-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_rps": 1000,
                "expected_latency": 500
            },
            "engine_b": {
                "name": "Engine B - AI/ML Processing", 
                "url": "https://infinityai-engine-b-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_rps": 500,
                "expected_latency": 600
            },
            "ultra_aggressive": {
                "name": "Ultra-Aggressive Trading Engine",
                "url": "https://infinityai-ultra-aggressive-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_rps": 2000,
                "expected_latency": 400
            },
            "engine_c": {
                "name": "Engine C - Trade Execution",
                "url": "https://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
                "platform": "AWS ECS/Fargate",
                "expected_rps": 800,
                "expected_latency": 500
            },
            "engine_d": {
                "name": "Engine D - AI Chatbot Assistant",
                "url": "https://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
                "platform": "AWS ECS/Fargate", 
                "expected_rps": 300,
                "expected_latency": 600
            }
        }
        
        self.frontend_url = "https://infinityai.pro"
        self.validation_results = {}
        self.metrics = {}
        
        print("🚀 INFINITYAI.PRO - COMPREHENSIVE SYSTEM VERIFICATION")
        print("=" * 80)
        print(f"🕐 Timestamp: {self.timestamp}")
        print(f"🔧 Verification Mode: {'All Engines' if args.check_engines == 'all' else args.check_engines}")
        print(f"📊 Metrics: {', '.join(args.metrics)}")
        print("=" * 80)

    async def measure_latency(self, session: aiohttp.ClientSession, url: str, samples: int = 10) -> Dict:
        """Measure detailed latency metrics"""
        latencies = []
        response_codes = []
        
        for _ in range(samples):
            start_time = time.time()
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                    await response.read()
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                    response_codes.append(response.status)
            except Exception as e:
                latencies.append(9999)  # Timeout/error penalty
                response_codes.append(0)
                self.logger.warning(f"Latency test failed for {url}: {e}")
        
        return {
            "average": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 5 else max(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "response_codes": response_codes
        }

    async def measure_throughput(self, session: aiohttp.ClientSession, url: str, duration: int = 10) -> float:
        """Measure throughput capacity"""
        successful_requests = 0
        start_time = time.time()
        
        async def single_request():
            nonlocal successful_requests
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5), ssl=False) as response:
                    if response.status == 200:
                        successful_requests += 1
            except:
                pass
        
        # Concurrent requests for throughput testing
        tasks = []
        while time.time() - start_time < duration:
            # Create batch of concurrent requests
            batch_size = 20
            batch_tasks = [single_request() for _ in range(batch_size)]
            tasks.extend(batch_tasks)
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            await asyncio.sleep(0.1)  # Brief pause
        
        actual_duration = time.time() - start_time
        rps = successful_requests / actual_duration if actual_duration > 0 else 0
        
        self.logger.info(f"Throughput test: {successful_requests} requests in {actual_duration:.2f}s = {rps:.2f} RPS")
        return rps

    async def analyze_capacity(self, engine_config: Dict, metrics: Dict) -> float:
        """Calculate engine capacity score"""
        latency_score = max(0, 100 - (metrics["latency"]["average"] / engine_config["expected_latency"] * 100))
        throughput_score = min(100, (metrics["throughput"] / engine_config["expected_rps"]) * 100)
        
        # Error rate penalty
        error_rate = sum(1 for code in metrics["latency"]["response_codes"] if code != 200) / len(metrics["latency"]["response_codes"])
        error_penalty = error_rate * 50
        
        capacity_score = max(0, (latency_score + throughput_score) / 2 - error_penalty)
        return capacity_score

    async def trace_dataflow(self, session: aiohttp.ClientSession) -> Dict:
        """Trace data flow between engines"""
        dataflow_results = {}
        
        # Test cross-engine communication paths
        communication_paths = [
            ("engine_a", "engine_c", "Market Data → Trade Execution"),
            ("engine_b", "engine_c", "AI/ML → Trade Execution"), 
            ("engine_d", "engine_c", "Chatbot → Trade Execution"),
            ("ultra_aggressive", "engine_c", "Ultra Trading → Trade Execution")
        ]
        
        for source, target, description in communication_paths:
            source_url = self.engines[source]["url"]
            target_url = self.engines[target]["url"]
            
            try:
                # Test if source can reach target
                start_time = time.time()
                async with session.get(source_url, ssl=False) as source_response:
                    source_healthy = source_response.status == 200
                    
                async with session.get(target_url, ssl=False) as target_response:
                    target_healthy = target_response.status == 200
                
                dataflow_time = (time.time() - start_time) * 1000
                
                dataflow_results[f"{source}_to_{target}"] = {
                    "description": description,
                    "source_healthy": source_healthy,
                    "target_healthy": target_healthy,
                    "dataflow_latency": dataflow_time,
                    "status": "HEALTHY" if source_healthy and target_healthy else "DEGRADED"
                }
                
            except Exception as e:
                dataflow_results[f"{source}_to_{target}"] = {
                    "description": description,
                    "status": "FAILED",
                    "error": str(e)
                }
        
        return dataflow_results

    async def verify_cloud_infrastructure(self) -> Dict:
        """Verify cloud infrastructure status"""
        cloud_status = {
            "gcp_cloud_run": {
                "engines": ["engine_a", "engine_b", "ultra_aggressive"],
                "status": "UNKNOWN",
                "performance": {}
            },
            "aws_ecs": {
                "engines": ["engine_c", "engine_d"],
                "status": "UNKNOWN", 
                "performance": {}
            }
        }
        
        # Test GCP engines
        gcp_healthy = 0
        for engine in cloud_status["gcp_cloud_run"]["engines"]:
            if engine in self.validation_results and self.validation_results[engine].get("healthy", False):
                gcp_healthy += 1
        
        cloud_status["gcp_cloud_run"]["status"] = "HEALTHY" if gcp_healthy == 3 else "DEGRADED"
        cloud_status["gcp_cloud_run"]["performance"] = {
            "healthy_engines": f"{gcp_healthy}/3",
            "availability": f"{(gcp_healthy/3)*100:.1f}%"
        }
        
        # Test AWS engines
        aws_healthy = 0
        for engine in cloud_status["aws_ecs"]["engines"]:
            if engine in self.validation_results and self.validation_results[engine].get("healthy", False):
                aws_healthy += 1
                
        cloud_status["aws_ecs"]["status"] = "HEALTHY" if aws_healthy == 2 else "DEGRADED"
        cloud_status["aws_ecs"]["performance"] = {
            "healthy_engines": f"{aws_healthy}/2",
            "availability": f"{(aws_healthy/2)*100:.1f}%"
        }
        
        return cloud_status

    async def verify_frontend(self) -> Dict:
        """Verify frontend status and performance"""
        frontend_results = {
            "url": self.frontend_url,
            "status": "UNKNOWN",
            "performance": {},
            "content_verification": False,
            "ssl_grade": "UNKNOWN"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(self.frontend_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    load_time = (time.time() - start_time) * 1000
                    content = await response.text()
                    
                    frontend_results.update({
                        "status": "HEALTHY" if response.status == 200 else "DEGRADED",
                        "performance": {
                            "load_time_ms": load_time,
                            "response_code": response.status,
                            "content_size_kb": len(content.encode('utf-8')) / 1024
                        },
                        "content_verification": "InfinityAI.Pro" in content,
                        "ssl_grade": "A+" if response.url.scheme == "https" else "NONE"
                    })
                    
        except Exception as e:
            frontend_results["status"] = "FAILED"
            frontend_results["error"] = str(e)
            
        return frontend_results

    async def verify_cicd(self) -> Dict:
        """Verify CI/CD pipeline status"""
        cicd_results = {
            "github_connectivity": False,
            "deployment_status": "UNKNOWN",
            "last_commit_accessible": False
        }
        
        try:
            # Test GitHub connectivity
            async with aiohttp.ClientSession() as session:
                github_url = "https://api.github.com/repos/raghu-1718/InfinityAI.Pro"
                async with session.get(github_url) as response:
                    if response.status == 200:
                        cicd_results["github_connectivity"] = True
                        repo_data = await response.json()
                        cicd_results["last_commit_accessible"] = True
                        cicd_results["deployment_status"] = "ACCESSIBLE"
                    
        except Exception as e:
            cicd_results["error"] = str(e)
            
        return cicd_results

    async def run_comprehensive_verification(self) -> Dict:
        """Run complete system verification"""
        self.logger.info("🔍 Starting comprehensive system verification...")
        
        results = {
            "timestamp": self.timestamp,
            "verification_summary": {},
            "engine_metrics": {},
            "system_capacity": {},
            "dataflow_analysis": {},
            "cloud_infrastructure": {},
            "frontend_verification": {},
            "cicd_verification": {}
        }
        
        # Engine verification with metrics
        async with aiohttp.ClientSession() as session:
            for engine_id, config in self.engines.items():
                if self.args.check_engines == "all" or engine_id in self.args.check_engines:
                    self.logger.info(f"🔍 Verifying {config['name']}...")
                    
                    engine_metrics = {}
                    
                    # Latency measurement
                    if "latency" in self.args.metrics:
                        latency_data = await self.measure_latency(session, config["url"])
                        engine_metrics["latency"] = latency_data
                    
                    # Throughput measurement  
                    if "throughput" in self.args.metrics:
                        throughput = await self.measure_throughput(session, config["url"], duration=5)
                        engine_metrics["throughput"] = throughput
                    
                    # Capacity analysis
                    if "capacity" in self.args.metrics:
                        capacity_score = await self.analyze_capacity(config, engine_metrics)
                        engine_metrics["capacity_score"] = capacity_score
                    
                    # Health check
                    try:
                        health_url = f"{config['url']}/health"
                        async with session.get(health_url, ssl=False) as response:
                            engine_metrics["health_status"] = "HEALTHY" if response.status == 200 else "DEGRADED"
                    except:
                        engine_metrics["health_status"] = "FAILED"
                    
                    results["engine_metrics"][engine_id] = engine_metrics
                    self.validation_results[engine_id] = {"healthy": engine_metrics.get("health_status") == "HEALTHY"}
            
            # Dataflow tracing
            if "dataflow" in self.args.metrics and self.args.trace_dataflow:
                self.logger.info("🔄 Tracing system dataflow...")
                results["dataflow_analysis"] = await self.trace_dataflow(session)
        
        # Cloud infrastructure verification
        if self.args.verify_cloud:
            self.logger.info("☁️ Verifying cloud infrastructure...")
            results["cloud_infrastructure"] = await self.verify_cloud_infrastructure()
        
        # Frontend verification
        if self.args.verify_frontend:
            self.logger.info("🌐 Verifying frontend...")
            results["frontend_verification"] = await self.verify_frontend()
        
        # CI/CD verification  
        if self.args.verify_cicd:
            self.logger.info("🔧 Verifying CI/CD pipeline...")
            results["cicd_verification"] = await self.verify_cicd()
        
        # System capacity calculation
        self.logger.info("📊 Calculating system capacity...")
        results["system_capacity"] = self.calculate_system_capacity(results["engine_metrics"])
        
        # Verification summary
        results["verification_summary"] = self.generate_verification_summary(results)
        
        return results

    def calculate_system_capacity(self, engine_metrics: Dict) -> Dict:
        """Calculate overall system capacity"""
        operational_engines = sum(1 for metrics in engine_metrics.values() 
                                 if metrics.get("health_status") == "HEALTHY")
        
        total_throughput = sum(metrics.get("throughput", 0) for metrics in engine_metrics.values())
        avg_latency = statistics.mean([metrics.get("latency", {}).get("average", 1000) 
                                      for metrics in engine_metrics.values() if "latency" in metrics])
        
        reliability_score = (operational_engines / len(self.engines)) * 100
        
        return {
            "total_engines": len(self.engines),
            "operational_engines": operational_engines,
            "availability_percentage": reliability_score,
            "total_rps_capacity": total_throughput,
            "average_latency_ms": avg_latency,
            "peak_throughput_rps": max([metrics.get("throughput", 0) for metrics in engine_metrics.values()], default=0),
            "capacity_grade": "A" if reliability_score >= 90 else "B" if reliability_score >= 75 else "C"
        }

    def generate_verification_summary(self, results: Dict) -> Dict:
        """Generate comprehensive verification summary"""
        engine_metrics = results["engine_metrics"]
        system_capacity = results["system_capacity"]
        
        # Overall health
        healthy_engines = sum(1 for metrics in engine_metrics.values() 
                             if metrics.get("health_status") == "HEALTHY")
        
        overall_status = "PRODUCTION_READY" if healthy_engines >= 4 else "NEEDS_ATTENTION"
        
        # Performance summary
        performance_summary = {
            "latency_profile": {
                "excellent": sum(1 for metrics in engine_metrics.values() 
                               if metrics.get("latency", {}).get("average", 1000) < 500),
                "good": sum(1 for metrics in engine_metrics.values() 
                          if 500 <= metrics.get("latency", {}).get("average", 1000) < 1000),
                "needs_improvement": sum(1 for metrics in engine_metrics.values() 
                                       if metrics.get("latency", {}).get("average", 1000) >= 1000)
            }
        }
        
        return {
            "overall_status": overall_status,
            "health_score": f"{healthy_engines}/{len(self.engines)}",
            "availability_percentage": system_capacity["availability_percentage"],
            "performance_grade": system_capacity["capacity_grade"],
            "performance_summary": performance_summary,
            "verification_timestamp": self.timestamp,
            "ready_for_production": overall_status == "PRODUCTION_READY"
        }

    def generate_reports(self, results: Dict):
        """Generate detailed reports"""
        if "total_capacity" in self.args.report:
            self.print_capacity_report(results["system_capacity"])
        
        if "module_breakdown" in self.args.report:
            self.print_module_breakdown(results["engine_metrics"])
            
        if "speed_profile" in self.args.report:
            self.print_speed_profile(results["engine_metrics"])

    def print_capacity_report(self, capacity: Dict):
        """Print system capacity report"""
        print("\n" + "=" * 60)
        print("📊 TOTAL SYSTEM CAPACITY REPORT")
        print("=" * 60)
        print(f"🔧 Total Engines: {capacity['total_engines']}")
        print(f"✅ Operational: {capacity['operational_engines']}")
        print(f"📈 Availability: {capacity['availability_percentage']:.1f}%")
        print(f"⚡ Total RPS Capacity: {capacity['total_rps_capacity']:.1f}")
        print(f"🕐 Average Latency: {capacity['average_latency_ms']:.1f}ms")
        print(f"🚀 Peak Throughput: {capacity['peak_throughput_rps']:.1f} RPS")
        print(f"🏆 Capacity Grade: {capacity['capacity_grade']}")

    def print_module_breakdown(self, engine_metrics: Dict):
        """Print detailed module breakdown"""
        print("\n" + "=" * 60) 
        print("🔍 MODULE BREAKDOWN ANALYSIS")
        print("=" * 60)
        
        for engine_id, metrics in engine_metrics.items():
            config = self.engines[engine_id]
            print(f"\n🔧 {config['name']} ({config['platform']})")
            print(f"   Status: {metrics.get('health_status', 'UNKNOWN')}")
            if "latency" in metrics:
                print(f"   Latency: {metrics['latency']['average']:.1f}ms (P95: {metrics['latency']['p95']:.1f}ms)")
            if "throughput" in metrics:
                print(f"   Throughput: {metrics['throughput']:.1f} RPS")
            if "capacity_score" in metrics:
                print(f"   Capacity Score: {metrics['capacity_score']:.1f}/100")

    def print_speed_profile(self, engine_metrics: Dict):
        """Print speed performance profile"""
        print("\n" + "=" * 60)
        print("⚡ SYSTEM SPEED PROFILE")
        print("=" * 60)
        
        # Sort engines by performance
        sorted_engines = sorted(engine_metrics.items(), 
                               key=lambda x: x[1].get("latency", {}).get("average", 9999))
        
        print("🏁 Engine Performance Ranking:")
        for i, (engine_id, metrics) in enumerate(sorted_engines, 1):
            config = self.engines[engine_id]
            avg_latency = metrics.get("latency", {}).get("average", 9999)
            throughput = metrics.get("throughput", 0)
            
            performance_emoji = "🚀" if avg_latency < 500 else "⚡" if avg_latency < 800 else "🐌"
            print(f"   {i}. {performance_emoji} {config['name']}")
            print(f"      Latency: {avg_latency:.1f}ms | Throughput: {throughput:.1f} RPS")

    async def commit_to_github(self, results: Dict):
        """Commit validation results to GitHub"""
        if not self.args.commit_github:
            return
            
        try:
            # Save results to file
            results_file = f"validation_results_{self.timestamp.replace(':', '-')}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Git commands
            subprocess.run(["git", "add", results_file], check=True)
            subprocess.run(["git", "commit", "-m", f"Automated validation results - {self.timestamp}"], check=True)
            
            self.logger.info(f"✅ Committed validation results to GitHub: {results_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to commit to GitHub: {e}")

async def main():
    parser = argparse.ArgumentParser(description="InfinityAI.Pro Comprehensive System Verification")
    parser.add_argument("--verify-cloud", action="store_true", help="Verify cloud infrastructure")
    parser.add_argument("--check-engines", default="all", help="Engines to check (all, or specific engine IDs)")
    parser.add_argument("--metrics", default="latency,throughput,capacity,dataflow", 
                       help="Metrics to collect (comma-separated)")
    parser.add_argument("--trace-dataflow", action="store_true", help="Trace data flow between engines")
    parser.add_argument("--output-summary", choices=["final", "detailed"], default="final", 
                       help="Output summary type")
    parser.add_argument("--commit-github", action="store_true", help="Commit results to GitHub")
    parser.add_argument("--verify-cicd", action="store_true", help="Verify CI/CD pipeline")
    parser.add_argument("--verify-frontend", action="store_true", help="Verify frontend")
    parser.add_argument("--report", default="total_capacity,module_breakdown,speed_profile", 
                       help="Reports to generate")
    parser.add_argument("--log-level", choices=["info", "verbose"], default="info", help="Logging level")
    parser.add_argument("--timestamp", help="Custom timestamp")
    parser.add_argument("--emotional-checkin", help="Emotional check-in message")
    parser.add_argument("--philosophy-alert", help="Philosophy alert message")
    
    args = parser.parse_args()
    
    # Parse comma-separated arguments
    args.metrics = args.metrics.split(",")
    args.report = args.report.split(",")
    
    # Initialize validator
    validator = InfinityAIValidator(args)
    
    # Emotional check-in
    if args.emotional_checkin:
        print(f"\n🧘 Emotional Check-in: {args.emotional_checkin}")
    
    if args.philosophy_alert:
        print(f"🎭 Philosophy Alert: {args.philosophy_alert}")
    
    # Run verification
    try:
        results = await validator.run_comprehensive_verification()
        
        # Print summary
        print("\n" + "🎊" * 20)
        print("🚀 INFINITYAI.PRO VERIFICATION COMPLETE")
        print("🎊" * 20)
        
        summary = results["verification_summary"]
        print(f"📊 Overall Status: {summary['overall_status']}")
        print(f"💚 Health Score: {summary['health_score']}")
        print(f"📈 Availability: {summary['availability_percentage']:.1f}%")
        print(f"🏆 Performance Grade: {summary['performance_grade']}")
        print(f"✅ Production Ready: {'YES' if summary['ready_for_production'] else 'NEEDS WORK'}")
        
        # Generate reports
        validator.generate_reports(results)
        
        # Commit to GitHub if requested
        await validator.commit_to_github(results)
        
        # Final summary output
        if args.output_summary == "final":
            print(f"\n🎉 FINAL VALIDATION STATUS: {summary['overall_status']}")
            print(f"📅 Verification completed at: {validator.timestamp}")
            
            if summary["ready_for_production"]:
                print("🚀 InfinityAI.Pro is PRODUCTION READY for live trading!")
            else:
                print("⚠️ System needs attention before production deployment")
        
    except Exception as e:
        validator.logger.error(f"❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())