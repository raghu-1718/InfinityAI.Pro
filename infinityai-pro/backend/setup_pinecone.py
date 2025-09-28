#!/usr/bin/env python3
"""
Pinecone Setup Script for InfinityAI.Pro
Creates and configures Pinecone index for vector storage
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_pinecone_index():
    """Set up Pinecone index for InfinityAI.Pro"""

    try:
        from pinecone import Pinecone, ServerlessSpec

        # Get configuration
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "infinityai-vectors")
        dimension = int(os.getenv("VECTOR_DIMENSION", "384"))

        if not api_key:
            print("❌ PINECONE_API_KEY not found in environment variables")
            return False

        print("🔗 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)

        # Check if index already exists
        existing_indexes = pc.list_indexes().names()
        print(f"📋 Existing indexes: {existing_indexes}")

        if index_name in existing_indexes:
            print(f"✅ Index '{index_name}' already exists")
            index = pc.Index(index_name)

            # Check index stats
            stats = index.describe_index_stats()
            print(f"📊 Index stats: {stats}")

            return True

        # Create new index
        print(f"🏗️  Creating index '{index_name}' with {dimension} dimensions...")

        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print("⏳ Waiting for index to be ready...")
        time.sleep(10)  # Wait for index to initialize

        # Verify index creation
        indexes = pc.list_indexes().names()
        if index_name in indexes:
            print(f"✅ Index '{index_name}' created successfully!")

            # Get index stats
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"📊 Index stats: {stats}")

            return True
        else:
            print(f"❌ Failed to create index '{index_name}'")
            return False

    except ImportError:
        print("❌ Pinecone package not installed. Run: pip install pinecone-client")
        return False
    except Exception as e:
        print(f"❌ Error setting up Pinecone: {e}")
        return False

def test_pinecone_connection():
    """Test Pinecone connection and basic operations"""

    try:
        from pinecone import Pinecone
        import numpy as np

        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "infinityai-vectors")

        if not api_key:
            print("❌ PINECONE_API_KEY not found")
            return False

        print("🧪 Testing Pinecone connection...")

        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        # Test upsert
        test_vector = np.random.rand(384).astype(np.float32).tolist()
        test_id = "test-vector-123"
        test_metadata = {"type": "test", "timestamp": "2025-01-28"}

        index.upsert(vectors=[{
            "id": test_id,
            "values": test_vector,
            "metadata": test_metadata
        }])

        print("✅ Test vector upserted")

        # Test search
        results = index.query(
            vector=test_vector,
            top_k=1,
            include_metadata=True
        )

        if results.matches and results.matches[0].id == test_id:
            print("✅ Test search successful")
        else:
            print("❌ Test search failed")
            return False

        # Clean up test vector
        index.delete(ids=[test_id])
        print("🧹 Test vector cleaned up")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Pinecone for InfinityAI.Pro")
    print("=" * 50)

    # Setup index
    if setup_pinecone_index():
        print("\n🧪 Testing connection...")
        if test_pinecone_connection():
            print("\n🎉 Pinecone setup complete and tested!")
            print("💡 Your vector database is ready for InfinityAI.Pro")
            print("📝 Next: Configure other cloud services in .env file")
        else:
            print("\n❌ Connection test failed. Check your configuration.")
            sys.exit(1)
    else:
        print("\n❌ Pinecone setup failed.")
        sys.exit(1)