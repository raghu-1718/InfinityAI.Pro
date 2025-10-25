#!/usr/bin/env python3
"""
InfinityAI.Pro - GitHub Actions Workflow Analyzer
Analyzes CI/CD pipeline configuration and status
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List
import json


def analyze_workflow_file(workflow_path: Path) -> Dict:
    """Analyze a single workflow file"""
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        analysis = {
            "name": workflow.get("name", workflow_path.stem),
            "file": workflow_path.name,
            "triggers": [],
            "jobs": [],
            "uses_secrets": False,
            "deploys_to_gcp": False,
            "runs_tests": False
        }
        
        # Analyze triggers
        if "on" in workflow:
            triggers = workflow["on"]
            if isinstance(triggers, dict):
                analysis["triggers"] = list(triggers.keys())
            elif isinstance(triggers, list):
                analysis["triggers"] = triggers
            elif isinstance(triggers, str):
                analysis["triggers"] = [triggers]
        
        # Analyze jobs
        if "jobs" in workflow:
            for job_name, job_config in workflow["jobs"].items():
                job_info = {
                    "name": job_name,
                    "runs_on": job_config.get("runs-on", "unknown"),
                    "steps": len(job_config.get("steps", []))
                }
                analysis["jobs"].append(job_info)
                
                # Check for secrets usage
                job_str = str(job_config)
                if "${{ secrets." in job_str:
                    analysis["uses_secrets"] = True
                
                # Check for GCP deployment
                if "gcloud" in job_str.lower() or "cloud run" in job_str.lower():
                    analysis["deploys_to_gcp"] = True
                
                # Check for tests
                if "test" in job_str.lower() or "pytest" in job_str.lower() or "npm test" in job_str.lower():
                    analysis["runs_tests"] = True
        
        return analysis
    
    except Exception as e:
        return {
            "name": workflow_path.stem,
            "file": workflow_path.name,
            "error": str(e)
        }


def analyze_all_workflows() -> Dict:
    """Analyze all GitHub Actions workflows"""
    workflows_dir = Path(".github/workflows")
    
    if not workflows_dir.exists():
        return {"error": "No .github/workflows directory found"}
    
    workflows = []
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    for workflow_file in workflow_files:
        analysis = analyze_workflow_file(workflow_file)
        workflows.append(analysis)
    
    # Summary statistics
    summary = {
        "total_workflows": len(workflows),
        "deployment_workflows": sum(1 for w in workflows if w.get("deploys_to_gcp", False)),
        "test_workflows": sum(1 for w in workflows if w.get("runs_tests", False)),
        "workflows_with_secrets": sum(1 for w in workflows if w.get("uses_secrets", False)),
        "workflow_details": workflows
    }
    
    return summary


def generate_workflow_report():
    """Generate a markdown report of workflow analysis"""
    print("=" * 80)
    print("GITHUB ACTIONS WORKFLOW ANALYSIS")
    print("=" * 80)
    
    analysis = analyze_all_workflows()
    
    if "error" in analysis:
        print(f"\nError: {analysis['error']}")
        return
    
    print(f"\n📊 Workflow Summary:")
    print(f"  Total Workflows: {analysis['total_workflows']}")
    print(f"  Deployment Workflows: {analysis['deployment_workflows']}")
    print(f"  Test Workflows: {analysis['test_workflows']}")
    print(f"  Workflows using Secrets: {analysis['workflows_with_secrets']}")
    
    print("\n📋 Workflow Details:\n")
    print(f"{'Workflow Name':<40} {'Jobs':<6} {'GCP':<5} {'Tests':<6} {'Secrets':<8}")
    print("-" * 80)
    
    for workflow in analysis["workflow_details"]:
        if "error" in workflow:
            print(f"{workflow['name']:<40} ERROR: {workflow['error']}")
            continue
        
        name = workflow["name"][:39]
        jobs = len(workflow["jobs"])
        gcp = "✅" if workflow["deploys_to_gcp"] else "❌"
        tests = "✅" if workflow["runs_tests"] else "❌"
        secrets = "✅" if workflow["uses_secrets"] else "❌"
        
        print(f"{name:<40} {jobs:<6} {gcp:<5} {tests:<6} {secrets:<8}")
    
    print("\n📁 Detailed Workflow Information:\n")
    
    for workflow in analysis["workflow_details"]:
        if "error" in workflow:
            continue
        
        print(f"\n🔹 {workflow['name']}")
        print(f"   File: {workflow['file']}")
        print(f"   Triggers: {', '.join(workflow['triggers'])}")
        print(f"   Jobs ({len(workflow['jobs'])}):")
        
        for job in workflow["jobs"]:
            print(f"     - {job['name']}: {job['steps']} steps (runs-on: {job['runs_on']})")
        
        features = []
        if workflow["deploys_to_gcp"]:
            features.append("GCP Deployment")
        if workflow["runs_tests"]:
            features.append("Testing")
        if workflow["uses_secrets"]:
            features.append("Uses Secrets")
        
        if features:
            print(f"   Features: {', '.join(features)}")
    
    # Save JSON report
    report_path = Path("github_actions_analysis.json")
    with open(report_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n✅ Analysis complete! Report saved to: {report_path}")
    
    # Generate recommendations
    print("\n💡 Recommendations:\n")
    
    if analysis["test_workflows"] == 0:
        print("  ⚠️  No test workflows detected. Consider adding automated testing.")
    
    if analysis["deployment_workflows"] < 5:
        print("  ℹ️  Limited deployment workflows. Current setup looks minimal.")
    
    if analysis["workflows_with_secrets"] > 0:
        print(f"  ✅ {analysis['workflows_with_secrets']} workflows properly use GitHub Secrets.")


if __name__ == "__main__":
    generate_workflow_report()
