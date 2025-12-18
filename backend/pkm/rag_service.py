import os
import weaviate
import hashlib
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_weaviate.vectorstores import WeaviateVectorStore

from backend.core.config import settings

class RAGService:
    def __init__(self):
        # 1. Initialize Embeddings
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing.")
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        
        # 2. Connect to Weaviate (Production Vector DB)
        auth_config = None
        if settings.WEAVIATE_API_KEY:
            auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)

        self.client = weaviate.Client(
            url=settings.WEAVIATE_URL,
            auth_client_secret=auth_config,
            additional_headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
        )
        
        self.index_name = "KnowledgeObject"
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensures the Weaviate class exists with correct properties."""
        if not self.client.schema.exists(self.index_name):
            class_obj = {
                "class": self.index_name,
                "vectorizer": "text2vec-openai", # Or 'none' if we push vectors manually
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "source", "dataType": ["text"]},
                    {"name": "user_id", "dataType": ["int"]}, # 0 = Global
                    {"name": "scope", "dataType": ["text"]},  # 'private' vs 'global'
                    {"name": "content_hash", "dataType": ["text"]} # For deduplication
                ]
            }
            self.client.schema.create_class(class_obj)

    def ingest_text(self, text: str, source: str, user_id: int, metadata: Dict[str, Any] = None) -> int:
        """Chunks, hashes, and ingests text. Skips duplicates."""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        
        count = 0
        with self.client.batch as batch:
            batch.batch_size = 100
            for chunk in chunks:
                # 1. Deduplication Check
                content_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
                
                # Check if this specific chunk already exists for this scope
                exists = self.client.query.get(self.index_name, ["content_hash"]) \
                    .with_where({
                        "operator": "And",
                        "operands": [
                            {"path": ["content_hash"], "operator": "Equal", "valueText": content_hash},
                            {"path": ["user_id"], "operator": "Equal", "valueInt": user_id}
                        ]
                    }).with_limit(1).do()
                
                if exists['data']['Get'][self.index_name]:
                    continue # Skip duplicate

                # 2. Prepare Metadata
                props = {
                    "content": chunk,
                    "source": source,
                    "user_id": user_id,
                    "scope": "global" if user_id == 0 else "private",
                    "content_hash": content_hash,
                }
                if metadata:
                    props.update(metadata)

                # 3. Add to Batch
                # LangChain wrapper is good, but direct client gives more control over properties
                batch.add_data_object(props, self.index_name)
                count += 1
                
        return count
    
    def search(self, query: str, user_id: int, k: int = 5):
        """Performs Hybrid Search across Private (User) and Global (Shared) scopes."""
        # Weaviate Hybrid Search: Alpha 0.5 = Balance Keyword (BM25) and Vector
        response = (
            self.client.query
            .get(self.index_name, ["content", "source", "scope", "user_id"])
            .with_hybrid(query=query, alpha=0.5)
            .with_where({
                "operator": "Or",
                "operands": [
                    {"path": ["user_id"], "operator": "Equal", "valueInt": user_id}, # Private
                    {"path": ["user_id"], "operator": "Equal", "valueInt": 0}        # Global
                ]
            })
            .with_limit(k)
            .with_additional(["score", "distance"])
            .do()
        )
        
        results = []
        if 'data' in response and 'Get' in response['data']:
            items = response['data']['Get'][self.index_name]
            for item in items:
                results.append({
                    "content": item['content'],
                    "metadata": {"source": item['source'], "user_id": item['user_id']},
                    "scope": item['scope'],
                    "score": item['_additional']['score']
                })
        
        return results
    
rag_service = RAGService()