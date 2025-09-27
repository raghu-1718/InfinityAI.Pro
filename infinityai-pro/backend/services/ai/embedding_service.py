# services/ai/embedding_service.py
"""
InfinityAI.Pro - Embedding Service
SBERT embeddings with vector database for semantic search
"""

import os
import logging
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Embedding service with SBERT and vector database"""

    def __init__(self, sbert_config: Dict, vector_db_config: Dict):
        self.sbert_config = sbert_config
        self.vector_db_config = vector_db_config
        self.sbert_model = None
        self.vector_db = None
        self.initialized = False

    async def initialize(self):
        """Initialize SBERT and vector database"""
        try:
            # Check disk space before loading models
            try:
                import psutil
                disk = psutil.disk_usage('/')
                free_gb = disk.free / (1024**3)

                if free_gb < 1:  # Need at least 1GB free for SBERT
                    logger.warning(f"Insufficient disk space for SBERT model ({free_gb:.1f}GB free) - using fallback")
                    self.initialized = True
                    return
            except ImportError:
                logger.warning("psutil not available, proceeding without disk check")

            # Initialize SBERT
            logger.info(f"Loading SBERT model: {self.sbert_config['model']}")
            from sentence_transformers import SentenceTransformer
            self.sbert_model = SentenceTransformer(self.sbert_config['model'])

            # Initialize vector database
            await self._initialize_vector_db()

            self.initialized = True
            logger.info("✅ Embedding Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Embedding service: {e}")
            raise

    async def _initialize_vector_db(self):
        """Initialize vector database"""
        db_type = self.vector_db_config['type']

        if db_type == 'weaviate':
            await self._init_weaviate()
        elif db_type == 'chromadb':
            await self._init_chromadb()
        elif db_type == 'faiss':
            await self._init_faiss()
        else:
            logger.warning(f"Unknown vector DB type: {db_type}, using in-memory fallback")
            self.vector_db = {"type": "memory", "data": {}}

    async def _init_weaviate(self):
        """Initialize Weaviate client"""
        try:
            import weaviate

            self.vector_db = {
                "type": "weaviate",
                "client": weaviate.Client(self.vector_db_config['url'])
            }

            # Create schema if it doesn't exist
            collection = self.vector_db_config['collection']
            if not self.vector_db["client"].schema.contains({"class": collection}):
                self.vector_db["client"].schema.create_class({
                    "class": collection,
                    "properties": [
                        {"name": "text", "dataType": ["text"]},
                        {"name": "metadata", "dataType": ["object"]},
                        {"name": "timestamp", "dataType": ["date"]}
                    ]
                })

            logger.info(f"Weaviate initialized with collection: {collection}")

        except Exception as e:
            logger.warning(f"Weaviate not available: {e}, falling back to memory")
            self.vector_db = {"type": "memory", "data": {}}

    async def _init_chromadb(self):
        """Initialize ChromaDB client"""
        try:
            import chromadb

            self.vector_db = {
                "type": "chromadb",
                "client": chromadb.PersistentClient(path="./chroma_db")
            }

            # Create or get collection
            collection_name = self.vector_db_config['collection']
            self.vector_db["collection"] = self.vector_db["client"].get_or_create_collection(
                name=collection_name
            )

            logger.info(f"ChromaDB initialized with collection: {collection_name}")

        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}, falling back to memory")
            self.vector_db = {"type": "memory", "data": {}}

    async def _init_faiss(self):
        """Initialize FAISS index"""
        try:
            import faiss

            self.vector_db = {
                "type": "faiss",
                "index": faiss.IndexFlatIP(384),  # Cosine similarity for 384-dim embeddings
                "data": [],  # Store text and metadata
                "ids": []
            }

            logger.info("FAISS initialized")

        except Exception as e:
            logger.warning(f"FAISS not available: {e}, falling back to memory")
            self.vector_db = {"type": "memory", "data": {}}

    async def close(self):
        """Close embedding service"""
        # Vector DB clients don't need explicit closing
        pass

    async def embed_text(self, text: str, metadata: Dict = None) -> Dict:
        """Generate embeddings for text and optionally store"""
        try:
            if not self.initialized:
                raise RuntimeError("Embedding service not initialized")

            # Generate embedding
            embedding = self.sbert_model.encode(text).tolist()

            result = {
                "text": text,
                "embedding": embedding,
                "dimension": len(embedding),
                "model": self.sbert_config['model']
            }

            # Store if metadata provided
            if metadata:
                await self._store_embedding(text, embedding, metadata)
                result["stored"] = True
                result["id"] = metadata.get("id", f"doc_{len(self.vector_db.get('data', {}))}")

            result["timestamp"] = self._get_timestamp()
            return result

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return {"error": str(e)}

    async def _store_embedding(self, text: str, embedding: List[float], metadata: Dict):
        """Store embedding in vector database"""
        try:
            db_type = self.vector_db.get("type")

            if db_type == "weaviate":
                await self._store_weaviate(text, embedding, metadata)
            elif db_type == "chromadb":
                await self._store_chromadb(text, embedding, metadata)
            elif db_type == "faiss":
                await self._store_faiss(text, embedding, metadata)
            else:
                # Memory fallback
                doc_id = metadata.get("id", f"doc_{len(self.vector_db['data'])}")
                self.vector_db["data"][doc_id] = {
                    "text": text,
                    "embedding": embedding,
                    "metadata": metadata,
                    "timestamp": self._get_timestamp()
                }

        except Exception as e:
            logger.error(f"Error storing embedding: {e}")

    async def _store_weaviate(self, text: str, embedding: List[float], metadata: Dict):
        """Store in Weaviate"""
        collection = self.vector_db_config['collection']
        doc_data = {
            "text": text,
            "metadata": metadata,
            "timestamp": self._get_timestamp()
        }

        self.vector_db["client"].data_object.create(
            doc_data,
            collection,
            vector=embedding
        )

    async def _store_chromadb(self, text: str, embedding: List[float], metadata: Dict):
        """Store in ChromaDB"""
        doc_id = metadata.get("id", f"doc_{self.vector_db['collection'].count()}")

        self.vector_db["collection"].add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

    async def _store_faiss(self, text: str, embedding: List[float], metadata: Dict):
        """Store in FAISS"""
        doc_id = metadata.get("id", f"doc_{len(self.vector_db['data'])}")

        # Add to FAISS index
        embedding_np = np.array([embedding], dtype=np.float32)
        self.vector_db["index"].add(embedding_np)

        # Store data
        self.vector_db["data"].append({
            "id": doc_id,
            "text": text,
            "metadata": metadata,
            "timestamp": self._get_timestamp()
        })
        self.vector_db["ids"].append(doc_id)

    async def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar content"""
        try:
            if not self.initialized:
                raise RuntimeError("Embedding service not initialized")

            # Generate query embedding
            query_embedding = self.sbert_model.encode(query).tolist()

            # Search vector database
            results = await self._search_vector_db(query_embedding, limit)

            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return [{"error": str(e)}]

    async def _search_vector_db(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """Search vector database"""
        db_type = self.vector_db.get("type")

        if db_type == "weaviate":
            return await self._search_weaviate(query_embedding, limit)
        elif db_type == "chromadb":
            return await self._search_chromadb(query_embedding, limit)
        elif db_type == "faiss":
            return await self._search_faiss(query_embedding, limit)
        else:
            # Memory search
            return await self._search_memory(query_embedding, limit)

    async def _search_weaviate(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """Search Weaviate"""
        collection = self.vector_db_config['collection']

        result = self.vector_db["client"].query.get(
            collection, ["text", "metadata", "timestamp"]
        ).with_near_vector({
            "vector": query_embedding
        }).with_limit(limit).do()

        hits = result.get("data", {}).get("Get", {}).get(collection, [])
        return [{
            "text": hit["text"],
            "metadata": hit["metadata"],
            "timestamp": hit["timestamp"],
            "score": hit.get("_additional", {}).get("certainty", 0)
        } for hit in hits]

    async def _search_chromadb(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """Search ChromaDB"""
        results = self.vector_db["collection"].query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        return [{
            "text": doc,
            "metadata": meta,
            "id": doc_id,
            "score": score
        } for doc, meta, doc_id, score in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["ids"][0],
            results["distances"][0]
        )]

    async def _search_faiss(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """Search FAISS"""
        query_np = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.vector_db["index"].search(query_np, limit)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.vector_db["data"]):
                doc = self.vector_db["data"][idx]
                results.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": float(score),
                    "id": doc["id"]
                })

        return results

    async def _search_memory(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """Search in-memory storage"""
        import numpy as np

        results = []
        query_np = np.array(query_embedding)

        for doc_id, doc in self.vector_db["data"].items():
            doc_embedding = np.array(doc["embedding"])
            similarity = np.dot(query_np, doc_embedding) / (
                np.linalg.norm(query_np) * np.linalg.norm(doc_embedding)
            )

            results.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": float(similarity),
                "id": doc_id
            })

        # Sort by similarity and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def health_check(self) -> Dict:
        """Check embedding service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            health = {
                "status": "healthy",
                "sbert": {
                    "model": self.sbert_config['model'],
                    "available": self.sbert_model is not None
                },
                "vector_db": {
                    "type": self.vector_db_config['type'],
                    "available": self.vector_db is not None
                }
            }

            return health

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }