#!/usr/bin/env python3
"""
InfinityAI.Pro - Dependency Security Analyzer
Checks for known vulnerabilities in dependencies
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List


def check_python_dependencies(requirements_file: Path) -> Dict:
    """Check Python dependencies for vulnerabilities using pip-audit"""
    if not requirements_file.exists():
        return {"error": "File not found"}
    
    results = {
        "file": str(requirements_file),
        "total_packages": 0,
        "vulnerabilities": [],
        "outdated": []
    }
    
    # Count packages
    with open(requirements_file, 'r') as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        results["total_packages"] = len(packages)
    
    # Check for vulnerabilities using pip-audit (if installed)
    try:
        result = subprocess.run(
            ["pip-audit", "-r", str(requirements_file), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout:
            audit_data = json.loads(result.stdout)
            results["vulnerabilities"] = audit_data.get("vulnerabilities", [])
    except FileNotFoundError:
        results["note"] = "pip-audit not installed, skipping vulnerability check"
    except Exception as e:
        results["note"] = f"Could not run pip-audit: {str(e)}"
    
    return results


def check_npm_dependencies(package_json: Path) -> Dict:
    """Check NPM dependencies for vulnerabilities"""
    if not package_json.exists():
        return {"error": "File not found"}
    
    results = {
        "file": str(package_json),
        "total_packages": 0,
        "dependencies": {},
        "devDependencies": {},
        "vulnerabilities": []
    }
    
    # Read package.json
    with open(package_json, 'r') as f:
        pkg = json.load(f)
        results["dependencies"] = pkg.get("dependencies", {})
        results["devDependencies"] = pkg.get("devDependencies", {})
        results["total_packages"] = len(results["dependencies"]) + len(results["devDependencies"])
    
    # Check for vulnerabilities using npm audit (if available)
    package_dir = package_json.parent
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=package_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout:
            audit_data = json.loads(result.stdout)
            if "vulnerabilities" in audit_data:
                results["audit_summary"] = audit_data.get("metadata", {}).get("vulnerabilities", {})
    except FileNotFoundError:
        results["note"] = "npm not available"
    except Exception as e:
        results["note"] = f"Could not run npm audit: {str(e)}"
    
    return results


def analyze_all_dependencies():
    """Analyze all dependencies in the project"""
    print("=" * 80)
    print("DEPENDENCY SECURITY ANALYSIS")
    print("=" * 80)
    
    project_root = Path.cwd()
    all_results = {
        "python_dependencies": [],
        "npm_dependencies": [],
        "summary": {
            "total_python_packages": 0,
            "total_npm_packages": 0,
            "python_vulnerabilities": 0,
            "npm_vulnerabilities": 0
        }
    }
    
    # Check Python dependencies in engines
    print("\n🐍 Python Dependencies:\n")
    for engine in ["engine-a", "engine-b", "engine-c-execution", "engine-d"]:
        req_file = project_root / "engines" / engine / "requirements.txt"
        if req_file.exists():
            print(f"  Analyzing {engine}...")
            results = check_python_dependencies(req_file)
            all_results["python_dependencies"].append(results)
            all_results["summary"]["total_python_packages"] += results.get("total_packages", 0)
            
            if results.get("vulnerabilities"):
                all_results["summary"]["python_vulnerabilities"] += len(results["vulnerabilities"])
                print(f"    ⚠️  Found {len(results['vulnerabilities'])} vulnerabilities")
            else:
                print(f"    ✅ {results.get('total_packages', 0)} packages")
    
    # Check NPM dependencies
    print("\n📦 NPM Dependencies:\n")
    
    npm_locations = [
        ("root", project_root / "package.json"),
        ("frontend", project_root / "frontend" / "package.json"),
        ("functions", project_root / "functions" / "package.json")
    ]
    
    for name, pkg_json in npm_locations:
        if pkg_json.exists():
            print(f"  Analyzing {name}...")
            results = check_npm_dependencies(pkg_json)
            all_results["npm_dependencies"].append(results)
            all_results["summary"]["total_npm_packages"] += results.get("total_packages", 0)
            
            audit_summary = results.get("audit_summary", {})
            if audit_summary:
                total_vulns = sum(audit_summary.values())
                all_results["summary"]["npm_vulnerabilities"] += total_vulns
                if total_vulns > 0:
                    print(f"    ⚠️  Vulnerabilities: {audit_summary}")
                else:
                    print(f"    ✅ {results.get('total_packages', 0)} packages, no vulnerabilities")
            else:
                print(f"    ✅ {results.get('total_packages', 0)} packages")
    
    # Save results
    output_file = project_root / "dependency_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n📊 Dependency Statistics:")
    print(f"  Total Python Packages: {all_results['summary']['total_python_packages']}")
    print(f"  Total NPM Packages: {all_results['summary']['total_npm_packages']}")
    print(f"  Python Vulnerabilities: {all_results['summary']['python_vulnerabilities']}")
    print(f"  NPM Vulnerabilities: {all_results['summary']['npm_vulnerabilities']}")
    
    print(f"\n✅ Analysis saved to: {output_file}")
    
    # Recommendations
    print("\n💡 Recommendations:\n")
    
    if all_results['summary']['python_vulnerabilities'] > 0:
        print("  🔴 CRITICAL: Python vulnerabilities detected. Run 'pip-audit -r requirements.txt' to see details.")
    
    if all_results['summary']['npm_vulnerabilities'] > 0:
        print("  🔴 CRITICAL: NPM vulnerabilities detected. Run 'npm audit fix' to attempt automatic fixes.")
    
    if all_results['summary']['python_vulnerabilities'] == 0 and all_results['summary']['npm_vulnerabilities'] == 0:
        print("  ✅ No vulnerabilities detected in dependencies!")
    
    print("\n  ℹ️  Note: Install 'pip-audit' for detailed Python vulnerability scanning:")
    print("     pip install pip-audit")


if __name__ == "__main__":
    analyze_all_dependencies()
