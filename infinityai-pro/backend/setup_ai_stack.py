#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete AI Stack Setup
Install and configure Ollama, models, and all AI services
"""

import os
import sys
import subprocess
import platform
import asyncio
from pathlib import Path

def run_command(cmd, shell=False, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd if shell else cmd.split(), shell=shell, check=check,
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, "", str(e)

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_step(step, text):
    """Print a step with number"""
    print(f"\n[{step}] {text}")

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"

async def setup_ollama():
    """Setup Ollama for local LLM"""
    print_header("Setting up Ollama (Local LLM)")

    os_type = detect_os()
    print(f"Detected OS: {os_type}")

    # Install Ollama based on OS
    if os_type == "macos":
        print_step("1", "Installing Ollama on macOS...")
        success, stdout, stderr = run_command("brew install ollama", shell=True, check=False)
        if not success:
            print("❌ Homebrew not found. Please install Homebrew first: https://brew.sh/")
            print("   Then run: brew install ollama")
            return False

    elif os_type == "linux":
        print_step("1", "Installing Ollama on Linux...")
        # Download and install Ollama
        success, stdout, stderr = run_command("curl -fsSL https://ollama.ai/install.sh | sh", shell=True, check=False)
        if not success:
            print("❌ Failed to install Ollama automatically")
            print("   Please visit: https://ollama.ai/download/linux")
            return False

    elif os_type == "windows":
        print_step("1", "Installing Ollama on Windows...")
        print("📥 Please download Ollama from: https://ollama.ai/download/windows")
        print("   Run the installer and continue with the setup")
        input("Press Enter when Ollama is installed...")

    else:
        print(f"❌ Unsupported OS: {os_type}")
        return False

    # Start Ollama service
    print_step("2", "Starting Ollama service...")
    success, stdout, stderr = run_command("ollama serve", check=False)
    if not success and "already running" not in stderr.lower():
        print("⚠️  Could not start Ollama service (might already be running)")

    # Download models
    print_step("3", "Downloading AI models...")

    models_to_download = [
        "llama3.2",  # Main LLM
        "mistral",   # Alternative LLM
    ]

    for model in models_to_download:
        print(f"   📥 Downloading {model}...")
        success, stdout, stderr = run_command(f"ollama pull {model}", check=False)
        if not success:
            print(f"   ⚠️  Failed to download {model}: {stderr}")
        else:
            print(f"   ✅ Downloaded {model}")

    # Test Ollama
    print_step("4", "Testing Ollama installation...")
    success, stdout, stderr = run_command("ollama list")
    if success:
        print("✅ Ollama is working!")
        print("Available models:")
        print(stdout)
    else:
        print("❌ Ollama test failed")
        return False

    return True

async def setup_python_deps():
    """Setup Python dependencies"""
    print_header("Setting up Python Dependencies")

    print_step("1", "Installing Python packages...")

    # Install requirements
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    if success:
        print("✅ Python dependencies installed")
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False

    # Test key imports
    print_step("2", "Testing key imports...")

    test_imports = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("sentence_transformers", "Sentence Transformers"),
        ("ultralytics", "Ultralytics (YOLO)"),
        ("whisper", "OpenAI Whisper"),
        ("diffusers", "Diffusers"),
    ]

    for module, name in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")

    return True

async def setup_vector_db():
    """Setup vector database (Weaviate or ChromaDB)"""
    print_header("Setting up Vector Database")

    print_step("1", "Choose vector database:")
    print("   1. Weaviate (Docker) - Recommended")
    print("   2. ChromaDB (Local) - Simple")
    print("   3. Skip for now")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        print_step("2", "Setting up Weaviate with Docker...")

        # Check if Docker is installed
        success, stdout, stderr = run_command("docker --version", check=False)
        if not success:
            print("❌ Docker not found. Please install Docker first.")
            print("   Visit: https://docs.docker.com/get-docker/")
            return False

        # Run Weaviate
        docker_cmd = """
        docker run -d \
          --name weaviate \
          -p 8080:8080 \
          -e QUERY_DEFAULTS_LIMIT=25 \
          -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
          -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
          semitechnologies/weaviate:latest
        """

        success, stdout, stderr = run_command(docker_cmd, shell=True, check=False)
        if success:
            print("✅ Weaviate started on port 8080")
            print("   Configure VECTOR_DB_URL=http://localhost:8080 in your environment")
        else:
            print(f"❌ Failed to start Weaviate: {stderr}")

    elif choice == "2":
        print_step("2", "ChromaDB will be used automatically (no setup needed)")
        print("   It will create a local database in ./chroma_db/")

    else:
        print("   Skipping vector database setup")

    return True

async def test_ai_stack():
    """Test the complete AI stack"""
    print_header("Testing AI Stack")

    print_step("1", "Testing AI Manager initialization...")

    try:
        # Change to backend directory
        os.chdir("backend")

        # Test AI manager
        from services.ai import ai_manager

        print("   Initializing AI services...")
        await ai_manager.initialize()

        print("   Testing health check...")
        health = await ai_manager.health_check()
        print(f"   Health status: {health.get('overall', 'unknown')}")

        # Test basic LLM chat
        print("   Testing LLM chat...")
        response = await ai_manager.chat("Hello, what can you help me with for trading?")
        if response and 'response' in response:
            print("   ✅ LLM chat working")
            print(f"   Response preview: {response['response'][:100]}...")
        else:
            print("   ❌ LLM chat failed")

        await ai_manager.close()
        print("✅ AI Stack test completed!")

    except Exception as e:
        print(f"❌ AI Stack test failed: {e}")
        return False

    return True

async def create_env_file():
    """Create environment configuration file"""
    print_header("Creating Environment Configuration")

    env_content = """# InfinityAI.Pro Environment Configuration
# Copy this to .env and configure your settings

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_LANGUAGE=en

# Stable Diffusion Configuration
DIFFUSERS_MODEL=stabilityai/stable-diffusion-2-1

# YOLO Configuration
YOLO_MODEL=yolov8n.pt

# Sentence Transformers Configuration
SBERT_MODEL=all-MiniLM-L6-v2

# Vector Database Configuration
VECTOR_DB=chromadb
VECTOR_DB_URL=http://localhost:8080
VECTOR_DB_COLLECTION=infinity_ai_docs

# Optional: Hugging Face token for additional models
# HF_TOKEN=your_huggingface_token_here
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env configuration file")
        print("   Edit .env to customize your AI stack settings")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

async def main():
    """Main setup function"""
    print("🚀 InfinityAI.Pro - Complete AI Stack Setup")
    print("=" * 60)
    print("This will install and configure:")
    print("• Ollama (Local LLM with LLaMA3/Mistral)")
    print("• Whisper (Speech-to-Text)")
    print("• Stable Diffusion (Image Generation)")
    print("• YOLOv8 (Object Detection)")
    print("• Sentence Transformers (Embeddings)")
    print("• Vector Database (Weaviate/ChromaDB)")
    print()

    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the backend directory")
        print("   cd infinityai-pro/backend")
        sys.exit(1)

    # Run setup steps
    steps = [
        ("Ollama Setup", setup_ollama),
        ("Python Dependencies", setup_python_deps),
        ("Vector Database", setup_vector_db),
        ("AI Stack Testing", test_ai_stack),
        ("Environment Config", create_env_file),
    ]

    for step_name, step_func in steps:
        try:
            success = await step_func()
            if not success:
                print(f"❌ {step_name} failed. Continuing with other steps...")
        except Exception as e:
            print(f"❌ {step_name} error: {e}")

    # Final instructions
    print_header("Setup Complete!")
    print("🎯 Next Steps:")
    print("1. Review and edit .env configuration file")
    print("2. Start the AI services:")
    print("   python services/ai/ai_manager.py")
    print("3. Run the trading system:")
    print("   python services/live_trader.py")
    print()
    print("📚 Useful Commands:")
    print("• List Ollama models: ollama list")
    print("• Pull new model: ollama pull <model_name>")
    print("• Test LLM: ollama run llama3.2")
    print()
    print("🎉 Your InfinityAI.Pro AI stack is ready!")

if __name__ == "__main__":
    asyncio.run(main())