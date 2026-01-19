"""
RAG Memory Engine - Semantic code search and storage using Weaviate.
"""
import weaviate
import hashlib
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter, MetadataQuery
from typing import List, Dict, Any, Optional
from loguru import logger
from openai import OpenAI

from app.core.config import settings


class RAGMemoryEngine:
    """
    Manages semantic code memory using vector database.
    Stores and retrieves code chunks with embeddings for context-aware chat.
    """
    
    def __init__(self):
        self.client: Optional[weaviate.WeaviateClient] = None
        self.openai_client: Optional[OpenAI] = None
        self.groq_client: Optional[OpenAI] = None
        self.collection_name = "CodeChunks"
        
        logger.info("RAG Memory Engine created")
    
    async def initialize(self) -> None:
        """Initialize connections to vector DB and embedding model."""
        try:
            # Connect to Weaviate using v4 API
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080
            )
            
            # Initialize OpenAI for embeddings
            if settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("Using OpenAI for embeddings (text-embedding-3-small)")

            # Initialize Groq for embeddings (OpenAI-compatible API)
            if settings.GROQ_API_KEY:
                self.groq_client = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1",
                )
                logger.info("Groq embeddings client initialized")
            
            # Create schema if it doesn't exist
            await self._ensure_schema()
            
            logger.info("✅ RAG Memory Engine initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize RAG Memory Engine: {e}")
            raise
    
    async def _ensure_schema(self) -> None:
        """Create Weaviate collection if it doesn't exist."""
        if not self.client:
            return
        
        # Check if collection exists
        try:
            if self.client.collections.exists(self.collection_name):
                logger.info(f"Collection {self.collection_name} already exists")
                return
        except Exception:
            pass
        
        # Create collection with v4 API
        self.client.collections.create(
            name=self.collection_name,
            description="Code chunks for RAG memory",
            vectorizer_config=Configure.Vectorizer.none(),  # We provide our own vectors
            properties=[
                Property(name="content", data_type=DataType.TEXT, description="The actual code/text content"),
                Property(name="file_path", data_type=DataType.TEXT, description="Path to source file"),
                Property(name="language", data_type=DataType.TEXT, description="Programming language"),
                Property(name="start_line", data_type=DataType.INT, description="Starting line number"),
                Property(name="end_line", data_type=DataType.INT, description="Ending line number"),
                Property(name="project_id", data_type=DataType.TEXT, description="Project identifier"),
                Property(name="chunk_type", data_type=DataType.TEXT, description="Type of chunk (function, class, comment, etc.)"),
            ],
        )
        logger.info(f"Created collection: {self.collection_name}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using configured provider."""
        provider = settings.EMBEDDING_PROVIDER.lower()

        if provider == "groq":
            model = settings.GROQ_EMBEDDING_MODEL or settings.EMBEDDING_MODEL
            if self.groq_client:
                try:
                    response = self.groq_client.embeddings.create(
                        model=model,
                        input=text
                    )
                    return response.data[0].embedding
                except Exception as e:
                    logger.warning(f"Groq embedding failed: {e}")

        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}")

        # Fallback: deterministic hash embedding
        return self._hash_embedding(text, settings.EMBEDDING_DIMENSION)

    def _hash_embedding(self, text: str, dim: int) -> List[float]:
        """Deterministic lightweight embedding fallback (non-semantic)."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [((b / 255.0) * 2 - 1) for b in digest]
        # Repeat to reach dim
        out = (vals * (dim // len(vals) + 1))[:dim]
        return out
    
    async def add_document(
        self,
        content: str,
        file_path: str,
        language: str,
        project_id: str,
        start_line: int = 0,
        end_line: int = 0,
        chunk_type: str = "code",
    ) -> str:
        """Add a document chunk to the memory."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Generate embedding
        embedding = await self.embed_text(content)
        
        # Get collection
        collection = self.client.collections.get(self.collection_name)
        
        # Create data object
        data_object = {
            "content": content,
            "file_path": file_path,
            "language": language,
            "start_line": start_line,
            "end_line": end_line,
            "project_id": project_id,
            "chunk_type": chunk_type,
        }
        
        # Add to Weaviate with v4 API
        uuid = collection.data.insert(
            properties=data_object,
            vector=embedding,
        )
        
        logger.debug(f"Added document chunk: {file_path}:{start_line}-{end_line}")
        return str(uuid)
    
    async def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        mode: str = "vector",
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant code chunks.
        
        Args:
            query: Search query
            project_id: Optional project filter
            top_k: Number of results to return
            filters: Additional metadata filters
        
        Returns:
            List of matching code chunks with metadata and scores
        """
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        if mode not in {"vector", "bm25", "hybrid"}:
            mode = "vector"

        if mode == "bm25":
            return await self._search_bm25(query, project_id, top_k)

        if mode == "hybrid":
            return await self._search_hybrid(query, project_id, top_k)

        return await self._search_vector(query, project_id, top_k)

    async def _search_vector(
        self,
        query: str,
        project_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Vector search using embeddings."""
        # Generate query embedding
        try:
            query_embedding = await self.embed_text(query)
        except Exception as e:
            logger.warning(f"Vector embedding failed: {e}")
            raise

        collection = self.client.collections.get(self.collection_name)
        if project_id:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                filters=Filter.by_property("project_id").equal(project_id),
                return_metadata=MetadataQuery(distance=True, certainty=True)
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True, certainty=True)
            )

        return self._parse_vector_results(response)

    async def _search_bm25(
        self,
        query: str,
        project_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """BM25 keyword search using Weaviate inverted index."""
        try:
            collection = self.client.collections.get(self.collection_name)
            filters = Filter.by_property("project_id").equal(project_id) if project_id else None
            response = collection.query.bm25(
                query=query,
                limit=top_k,
                filters=filters,
                return_metadata=MetadataQuery(score=True)
            )
            return self._parse_bm25_results(response)
        except Exception as e:
            logger.warning(f"BM25 search failed, falling back to vector search: {e}")
            return await self._search_vector(query, project_id, top_k)

    async def _search_hybrid(
        self,
        query: str,
        project_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining vector and BM25 results."""
        vector_results: List[Dict[str, Any]] = []
        try:
            vector_results = await self._search_vector(query, project_id, top_k)
        except Exception:
            logger.warning("Vector search unavailable; falling back to BM25-only.")

        bm25_results = await self._search_bm25(query, project_id, top_k)

        merged: Dict[str, Dict[str, Any]] = {}

        def key(r: Dict[str, Any]) -> str:
            return f"{r.get('file_path')}:{r.get('start_line')}:{r.get('end_line')}"

        for r in vector_results:
            r["source"] = "vector"
            merged[key(r)] = r

        for r in bm25_results:
            r["source"] = "bm25"
            k = key(r)
            if k in merged:
                # Prefer higher score
                if r.get("score", 0) > merged[k].get("score", 0):
                    merged[k] = r
            else:
                merged[k] = r

        combined = list(merged.values())
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        return combined[:top_k]

    def _parse_vector_results(self, response) -> List[Dict[str, Any]]:
        chunks = []
        for item in response.objects:
            chunks.append({
                "content": item.properties.get("content", ""),
                "file_path": item.properties.get("file_path", ""),
                "language": item.properties.get("language", ""),
                "start_line": item.properties.get("start_line", 0),
                "end_line": item.properties.get("end_line", 0),
                "project_id": item.properties.get("project_id", ""),
                "chunk_type": item.properties.get("chunk_type", ""),
                "score": item.metadata.certainty if item.metadata.certainty else 0.0,
                "distance": item.metadata.distance if item.metadata.distance else 0.0,
            })
        return chunks

    def _parse_bm25_results(self, response) -> List[Dict[str, Any]]:
        chunks = []
        for item in response.objects:
            chunks.append({
                "content": item.properties.get("content", ""),
                "file_path": item.properties.get("file_path", ""),
                "language": item.properties.get("language", ""),
                "start_line": item.properties.get("start_line", 0),
                "end_line": item.properties.get("end_line", 0),
                "project_id": item.properties.get("project_id", ""),
                "chunk_type": item.properties.get("chunk_type", ""),
                "score": item.metadata.score if item.metadata.score else 0.0,
                "distance": 0.0,
            })
        return chunks
    
    async def delete_project(self, project_id: str) -> int:
        """Delete all chunks for a project."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        collection = self.client.collections.get(self.collection_name)
        
        # Delete with v4 API
        result = collection.data.delete_many(
            where=Filter.by_property("project_id").equal(project_id)
        )
        
        deleted_count = result.successful if result.successful else 0
        logger.info(f"Deleted {deleted_count} chunks for project {project_id}")
        return deleted_count
    
    async def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics about indexed project."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        collection = self.client.collections.get(self.collection_name)
        
        # Count with v4 API
        try:
            response = collection.aggregate.over_all(
                filters=Filter.by_property("project_id").equal(project_id),
                total_count=True
            )
            total_chunks = response.total_count if response.total_count else 0
        except Exception as e:
            logger.error(f"Error getting project stats: {e}")
            total_chunks = 0
        
        return {
            "project_id": project_id,
            "total_chunks": total_chunks,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.client:
            self.client.close()
        logger.info("RAG Memory Engine closed")
