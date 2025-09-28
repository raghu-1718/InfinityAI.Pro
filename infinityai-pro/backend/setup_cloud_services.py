#!/usr/bin/env python3
"""
Cloud Services Setup and Testing Script
Helps configure and test multi-cloud AI services for InfinityAI.Pro
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cloud_vector_service import cloud_vector_service
from services.cloud_ai_manager import cloud_ai_manager
from services.cloud_storage_service import cloud_storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_env_vars():
    """Check which environment variables are configured"""
    required_vars = {
        "Pinecone": ["PINECONE_API_KEY"],
        "Azure OpenAI": ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT"],
        "Azure Storage": ["AZURE_STORAGE_CONNECTION_STRING"],
        "AWS": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "Google Cloud": ["GOOGLE_CLOUD_PROJECT"]
    }

    print("🔍 Checking Environment Variables:")
    print("=" * 50)

    configured_services = 0
    total_services = len(required_vars)

    for service, vars in required_vars.items():
        all_configured = all(os.getenv(var) for var in vars)
        status = "✅ Configured" if all_configured else "❌ Missing"
        print(f"{service:15}: {status}")
        if all_configured:
            configured_services += 1

    print(f"\n📊 Services Configured: {configured_services}/{total_services}")
    return configured_services > 0

async def test_vector_db():
    """Test vector database connection"""
    print("\n🗄️  Testing Vector Database (Pinecone):")
    print("-" * 40)

    if cloud_vector_service.connect():
        stats = cloud_vector_service.get_stats()
        print("✅ Connected successfully")
        print(f"   Primary DB: {stats['primary_database']}")
        print(f"   Connected: {stats['connected']}")
        return True
    else:
        print("❌ Connection failed")
        return False

async def test_ai_services():
    """Test AI services"""
    print("\n🤖 Testing AI Services:")
    print("-" * 40)

    if await cloud_ai_manager.initialize():
        stats = cloud_ai_manager.get_service_status()
        print("✅ AI services initialized")
        print(f"   Total services: {stats['total_services']}")
        print(f"   Available: {stats['available_services']}")

        # Test text generation
        print("\n🧪 Testing text generation...")
        test_response = await cloud_ai_manager.generate_text(
            "Hello! This is a test of the multi-cloud AI system.",
            max_tokens=50
        )

        if test_response:
            print("✅ Text generation successful")
            print(f"   Response: {test_response[:100]}...")
        else:
            print("❌ Text generation failed")

        return True
    else:
        print("❌ AI services initialization failed")
        return False

async def test_storage():
    """Test cloud storage"""
    print("\n💾 Testing Cloud Storage:")
    print("-" * 40)

    if cloud_storage_service.connect():
        stats = cloud_storage_service.get_stats()
        print("✅ Storage connected")
        print(f"   Primary storage: {stats['primary_storage']}")
        print(f"   Connected: {stats['connected']}")
        return True
    else:
        print("❌ Storage connection failed")
        return False

def show_setup_instructions():
    """Show setup instructions for missing services"""
    print("\n🚀 SETUP INSTRUCTIONS:")
    print("=" * 50)

    instructions = {
        "Pinecone": """
1. Go to https://www.pinecone.io/
2. Sign up for free account
3. Create API key
4. Create index: 'infinityai-vectors' with 384 dimensions
5. Set environment variables:
   PINECONE_API_KEY=your_key
   PINECONE_ENVIRONMENT=gcp-starter
   PINECONE_INDEX_NAME=infinityai-vectors
""",

        "Azure OpenAI": """
1. Go to https://portal.azure.com/
2. Create 'Azure OpenAI' resource
3. Deploy GPT-4 model
4. Get API key and endpoint
5. Set environment variables:
   AZURE_OPENAI_KEY=your_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4
""",

        "Azure Storage": """
1. In Azure Portal, create 'Storage Account'
2. Get connection string from Access Keys
3. Set environment variable:
   AZURE_STORAGE_CONNECTION_STRING=your_connection_string
""",

        "AWS": """
1. Go to https://console.aws.amazon.com/
2. Create IAM user with programmatic access
3. Attach S3FullAccess policy
4. Get access keys
5. Create S3 bucket: 'infinityai-storage'
6. Set environment variables:
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_S3_BUCKET=infinityai-storage
""",

        "Google Cloud": """
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable Vertex AI API
4. Create service account with Vertex AI access
5. Download JSON key file
6. Set environment variables:
   GOOGLE_CLOUD_PROJECT=your_project_id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
"""
    }

    for service, instruction in instructions.items():
        print(f"\n{service}:{instruction}")

async def main():
    """Main setup and testing function"""
    print("🚀 InfinityAI.Pro Cloud Services Setup & Test")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check configuration
    has_config = check_env_vars()

    if not has_config:
        print("\n⚠️  No services configured. See setup instructions below.")
        show_setup_instructions()
        return

    # Test services
    print("\n🧪 TESTING SERVICES:")
    print("=" * 50)

    vector_ok = await test_vector_db()
    ai_ok = await test_ai_services()
    storage_ok = await test_storage()

    # Summary
    print("\n📊 TEST RESULTS:")
    print("-" * 40)
    print(f"Vector Database: {'✅ PASS' if vector_ok else '❌ FAIL'}")
    print(f"AI Services: {'✅ PASS' if ai_ok else '❌ FAIL'}")
    print(f"Cloud Storage: {'✅ PASS' if storage_ok else '❌ FAIL'}")

    working_services = sum([vector_ok, ai_ok, storage_ok])
    print(f"\n🎯 Overall: {working_services}/3 services working")

    if working_services == 3:
        print("\n🎉 ALL SYSTEMS GO! Your cloud AI infrastructure is ready!")
        print("💡 You can now run your FastAPI app with full cloud capabilities.")
    elif working_services > 0:
        print(f"\n✅ {working_services} service(s) working - partial functionality available.")
        print("💡 Configure remaining services for full functionality.")
    else:
        print("\n❌ No services working. Check your configuration and try again.")
        show_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main())