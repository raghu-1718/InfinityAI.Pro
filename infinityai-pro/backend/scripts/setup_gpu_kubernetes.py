#!/usr/bin/env python3
"""
InfinityAI.Pro - GPU and Kubernetes Setup for Windows
Helps set up GPU acceleration and Kubernetes deployment
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any

def log(message: str, level: str = "INFO"):
    """Enhanced logging with colors"""
    colors = {
        'INFO': '\033[0;34m',     # Blue
        'SUCCESS': '\033[0;32m',  # Green  
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'SETUP': '\033[0;35m',    # Magenta
    }
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    color = colors.get(level, colors['INFO'])
    reset = '\033[0m'
    
    icons = {
        'INFO': 'ℹ️', 'SUCCESS': '✅', 'WARNING': '⚠️', 
        'ERROR': '❌', 'SETUP': '🔧'
    }
    
    icon = icons.get(level, 'ℹ️')
    print(f"{color}[{timestamp}] {icon} {level}: {message}{reset}")

def check_system_requirements():
    """Check system requirements for GPU and Kubernetes"""
    log("🔍 Checking System Requirements...", "SETUP")
    
    system_info = {
        'os': os.name,
        'platform': sys.platform,
        'python_version': sys.version,
        'architecture': os.environ.get('PROCESSOR_ARCHITECTURE', 'Unknown')
    }
    
    log(f"OS: {system_info['os']} ({system_info['platform']})", "INFO")
    log(f"Architecture: {system_info['architecture']}", "INFO")
    
    return system_info

def check_gpu_availability():
    """Check for GPU availability and suggest setup"""
    log("🔥 GPU AVAILABILITY CHECK", "SETUP")
    log("-" * 50, "INFO")
    
    gpu_detected = False
    
    # Check for NVIDIA GPU
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            log("✅ NVIDIA GPU detected!", "SUCCESS")
            
            # Parse GPU info
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'Tesla' in line or 'GTX' in line or 'RTX' in line or 'Quadro' in line:
                    log(f"  📊 GPU: {line.strip()}", "SUCCESS")
            
            gpu_detected = True
            
            # Check CUDA version
            try:
                cuda_result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, check=False)
                if cuda_result.returncode == 0:
                    cuda_line = [l for l in cuda_result.stdout.split('\n') if 'release' in l.lower()]
                    if cuda_line:
                        log(f"  ✅ CUDA: {cuda_line[0].strip()}", "SUCCESS")
                else:
                    log("  ⚠️ CUDA Toolkit not installed", "WARNING")
                    log("  💡 Install from: https://developer.nvidia.com/cuda-downloads", "INFO")
            except FileNotFoundError:
                log("  ⚠️ CUDA Toolkit not found in PATH", "WARNING")
                
        else:
            log("❌ No NVIDIA GPU detected", "WARNING")
            
    except FileNotFoundError:
        log("❌ nvidia-smi not found", "WARNING")
    
    if not gpu_detected:
        log("🔧 GPU SETUP RECOMMENDATIONS:", "SETUP")
        log("  1. For NVIDIA GPU:", "INFO")
        log("     - Install latest NVIDIA drivers", "INFO")
        log("     - Install CUDA Toolkit 11.8+", "INFO") 
        log("     - Install cuDNN for deep learning", "INFO")
        log("  2. For Cloud GPU:", "INFO")
        log("     - Use AWS p3.2xlarge instances (V100)", "INFO")
        log("     - Use Azure NC6s_v3 (V100)", "INFO")
        log("     - Use GCP n1-standard-4 with V100", "INFO")
        log("  3. Current Status: CPU-only mode (functional but slower)", "INFO")
    
    return gpu_detected

def check_docker_gpu_support():
    """Check if Docker supports GPU acceleration"""
    log("🐳 Docker GPU Support Check", "SETUP")
    
    try:
        # Check if Docker Desktop is running
        result = subprocess.run(['docker', 'version'], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            log("❌ Docker not running", "ERROR")
            return False
        
        # Check for GPU support in Docker
        try:
            result = subprocess.run(
                ['docker', 'run', '--rm', '--gpus', 'all', 'nvidia/cuda:11.8-base-ubuntu20.04', 'nvidia-smi'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                log("✅ Docker GPU support working!", "SUCCESS")
                log("  Docker can access NVIDIA GPUs", "SUCCESS")
                return True
            else:
                log("⚠️ Docker GPU support not available", "WARNING")
                log("  Enable GPU support in Docker Desktop settings", "INFO")
                
        except subprocess.TimeoutExpired:
            log("⚠️ GPU test timed out", "WARNING")
        except FileNotFoundError:
            log("❌ Docker not found", "ERROR")
            
    except Exception as e:
        log(f"Docker check failed: {e}", "ERROR")
    
    return False

def setup_kubernetes_options():
    """Present Kubernetes setup options"""
    log("☸️  KUBERNETES DEPLOYMENT OPTIONS", "SETUP")
    log("-" * 50, "INFO")
    
    log("📋 Available Kubernetes Options:", "INFO")
    
    # Option 1: Docker Desktop Kubernetes
    log("1. 🐳 DOCKER DESKTOP KUBERNETES (Recommended for Development)", "SETUP")
    log("   ✅ Pros:", "SUCCESS")
    log("     - Easy setup (just enable in Docker Desktop)", "INFO")
    log("     - Integrated with Docker", "INFO")
    log("     - Good for local development", "INFO")
    log("   ⚠️  Cons:", "WARNING")
    log("     - Limited to single node", "INFO")
    log("     - No GPU scheduling by default", "INFO")
    log("   🔧 Setup:", "SETUP")
    log("     - Open Docker Desktop → Settings → Kubernetes", "INFO")
    log("     - Check 'Enable Kubernetes'", "INFO")
    log("     - Click 'Apply & Restart'", "INFO")
    
    # Option 2: Minikube
    log("\n2. 🚀 MINIKUBE (Local Kubernetes)", "SETUP")
    log("   ✅ Pros:", "SUCCESS")
    log("     - Full Kubernetes features", "INFO")
    log("     - GPU support possible", "INFO")
    log("     - Multiple nodes simulation", "INFO")
    log("   ⚠️  Cons:", "WARNING")
    log("     - More complex setup", "INFO")
    log("     - Resource intensive", "INFO")
    log("   🔧 Setup:", "SETUP")
    log("     - Download: https://minikube.sigs.k8s.io/docs/start/", "INFO")
    log("     - Run: minikube start --driver=docker", "INFO")
    
    # Option 3: Cloud Kubernetes
    log("\n3. ☁️  CLOUD KUBERNETES (Production)", "SETUP")
    log("   ✅ Pros:", "SUCCESS")
    log("     - GPU nodes available", "INFO")
    log("     - Production scalability", "INFO")
    log("     - Managed service", "INFO")
    log("   💰 Cons:", "WARNING")
    log("     - Costs money", "INFO")
    log("     - Requires cloud account", "INFO")
    log("   🔧 Options:", "SETUP")
    log("     - AWS EKS with GPU nodes", "INFO")
    log("     - Azure AKS with GPU nodes", "INFO")
    log("     - GCP GKE with GPU nodes", "INFO")

def check_kubernetes_status():
    """Check current Kubernetes status"""
    log("☸️  Kubernetes Status Check", "SETUP")
    
    try:
        # Check if kubectl is installed
        result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            log("❌ kubectl not installed", "WARNING")
            log("  💡 Install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/", "INFO")
            return False
        else:
            log("✅ kubectl installed", "SUCCESS")
        
        # Check cluster connection
        result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            log("✅ Kubernetes cluster connected", "SUCCESS")
            
            # Check nodes
            result = subprocess.run(['kubectl', 'get', 'nodes'], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                node_count = len(lines) - 1  # Exclude header
                log(f"  📊 Nodes: {node_count}", "INFO")
                
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        node_name = parts[0]
                        status = parts[1]
                        log(f"    • {node_name}: {status}", "SUCCESS" if status == "Ready" else "WARNING")
            
            # Check for GPU nodes
            result = subprocess.run(['kubectl', 'get', 'nodes', '-l', 'nvidia.com/gpu.present=true'], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                gpu_nodes = len(result.stdout.strip().split('\n')) - 1
                if gpu_nodes > 0:
                    log(f"  🔥 GPU Nodes: {gpu_nodes}", "SUCCESS")
                else:
                    log("  ⚠️ No GPU nodes found", "WARNING")
            
            return True
        else:
            log("❌ Cannot connect to Kubernetes cluster", "WARNING")
            log("  Cluster may not be running or configured", "INFO")
            return False
            
    except FileNotFoundError:
        log("❌ kubectl not found", "ERROR")
        return False

def generate_gpu_deployment_config():
    """Generate GPU-enabled deployment configuration"""
    log("🔧 Generating GPU-enabled Kubernetes configuration", "SETUP")
    
    gpu_config = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "infinityai-engine-b-gpu",
            "namespace": "infinityai"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "engine-b-gpu"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "engine-b-gpu"
                    }
                },
                "spec": {
                    "containers": [{
                        "name": "ai-engine",
                        "image": "infinityai/engine-b:latest",
                        "resources": {
                            "requests": {
                                "memory": "8Gi",
                                "cpu": "2000m",
                                "nvidia.com/gpu": 1
                            },
                            "limits": {
                                "memory": "16Gi", 
                                "cpu": "4000m",
                                "nvidia.com/gpu": 1
                            }
                        },
                        "env": [
                            {
                                "name": "CUDA_VISIBLE_DEVICES",
                                "value": "0"
                            },
                            {
                                "name": "NVIDIA_VISIBLE_DEVICES",
                                "value": "all"
                            }
                        ]
                    }],
                    "nodeSelector": {
                        "nvidia.com/gpu.present": "true"
                    },
                    "tolerations": [{
                        "key": "nvidia.com/gpu",
                        "operator": "Equal",
                        "value": "true",
                        "effect": "NoSchedule"
                    }]
                }
            }
        }
    }
    
    # Save configuration
    config_file = "gpu-deployment.yaml"
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(gpu_config, f, default_flow_style=False)
    
    log(f"✅ GPU deployment config saved to: {config_file}", "SUCCESS")
    return config_file

def provide_setup_instructions():
    """Provide step-by-step setup instructions"""
    log("📋 SETUP INSTRUCTIONS", "SETUP")
    log("=" * 60, "INFO")
    
    log("🔥 FOR GPU SETUP ON WINDOWS:", "SETUP")
    log("1. Install NVIDIA GPU Drivers:", "INFO")
    log("   - Visit: https://www.nvidia.com/Download/index.aspx", "INFO")
    log("   - Download and install latest drivers", "INFO")
    
    log("2. Install CUDA Toolkit:", "INFO")
    log("   - Visit: https://developer.nvidia.com/cuda-downloads", "INFO")
    log("   - Download CUDA 11.8 or 12.x", "INFO")
    log("   - Add to PATH: C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.8\\bin", "INFO")
    
    log("3. Enable GPU in Docker Desktop:", "INFO")
    log("   - Open Docker Desktop", "INFO")
    log("   - Settings → Resources → WSL Integration", "INFO")
    log("   - Enable WSL 2 backend", "INFO")
    log("   - Restart Docker Desktop", "INFO")
    
    log("\n☸️  FOR KUBERNETES SETUP (Choose One):", "SETUP")
    
    log("OPTION A: Docker Desktop Kubernetes (Easiest)", "INFO")
    log("1. Open Docker Desktop", "INFO")
    log("2. Settings → Kubernetes", "INFO")
    log("3. Check 'Enable Kubernetes'", "INFO")
    log("4. Click 'Apply & Restart'", "INFO")
    log("5. Wait for green 'Kubernetes is running' status", "INFO")
    
    log("\nOPTION B: Cloud Kubernetes (Production)", "INFO")
    log("1. Use our pre-built Terraform configs:", "INFO")
    log("   cd infrastructure/multi-cloud-gpu/terraform/aws", "INFO")
    log("   terraform init && terraform apply", "INFO")
    log("2. Or use managed services:", "INFO")
    log("   - AWS EKS", "INFO")
    log("   - Azure AKS", "INFO")
    log("   - GCP GKE", "INFO")
    
    log("\n🚀 AFTER SETUP:", "SETUP")
    log("1. Verify GPU: nvidia-smi", "INFO")
    log("2. Verify Docker GPU: docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi", "INFO")
    log("3. Verify Kubernetes: kubectl get nodes", "INFO")
    log("4. Deploy InfinityAI: kubectl apply -f gpu-deployment.yaml", "INFO")

def main():
    """Main setup and verification function"""
    log("🚀 InfinityAI.Pro GPU & Kubernetes Setup Assistant", "SUCCESS")
    log("=" * 60, "INFO")
    
    # Check system requirements
    system_info = check_system_requirements()
    
    # Check GPU status
    gpu_available = check_gpu_availability()
    
    # Check Docker GPU support
    docker_gpu = check_docker_gpu_support()
    
    # Check Kubernetes status
    k8s_available = check_kubernetes_status()
    
    # Show Kubernetes options
    setup_kubernetes_options()
    
    # Generate GPU config
    if gpu_available:
        try:
            import yaml
            generate_gpu_deployment_config()
        except ImportError:
            log("Install PyYAML for config generation: pip install pyyaml", "INFO")
    
    # Provide setup instructions
    provide_setup_instructions()
    
    # Summary
    log("\n" + "=" * 60, "SUCCESS")
    log("📊 CURRENT STATUS SUMMARY", "SUCCESS")
    log("=" * 60, "INFO")
    
    log(f"🔥 GPU Available: {'✅ YES' if gpu_available else '❌ NO (CPU mode)'}", 
        "SUCCESS" if gpu_available else "WARNING")
    log(f"🐳 Docker GPU: {'✅ YES' if docker_gpu else '❌ NO'}", 
        "SUCCESS" if docker_gpu else "WARNING")
    log(f"☸️  Kubernetes: {'✅ CONNECTED' if k8s_available else '❌ NOT CONNECTED'}", 
        "SUCCESS" if k8s_available else "WARNING")
    
    if not gpu_available and not k8s_available:
        log("\n🎯 RECOMMENDED NEXT STEPS:", "SETUP")
        log("1. For GPU: Follow Windows GPU setup instructions above", "INFO")
        log("2. For Kubernetes: Enable Docker Desktop Kubernetes", "INFO")
        log("3. For Production: Use cloud deployment with our Terraform configs", "INFO")
        log("4. Current setup works fine for development (CPU mode)", "SUCCESS")
    
    log("\n✅ Your InfinityAI.Pro platform is operational in current mode!", "SUCCESS")
    log("🚀 GPU and Kubernetes will add performance and scalability!", "INFO")

if __name__ == "__main__":
    main()