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
        """
        Defines two classes:
        1. AtomicNote: High-level summaries.
        2. RawChunk: The actual text segments.
        """
        # Class 1: Atomic Note (The Summary)
        if not self.client.schema.exists("AtomicNote"):
            self.client.schema.create_class({
                "class": "AtomicNote",
                "vectorizer": "text2vec-openai",
                "properties": [
                    {"name": "content", "dataType": ["text"]},    # The Summary
                    {"name": "source_url", "dataType": ["text"]}, # Origin
                    {"name": "title", "dataType": ["text"]},
                    {"name": "user_id", "dataType": ["int"]},     # 0 = Global
                    {"name": "scope", "dataType": ["text"]},      # 'global' / 'private'
                    {"name": "doc_id", "dataType": ["text"]},     # Unique Link ID
                    {"name": "has_raw", "dataType": ["boolean"]}  # Does raw data exist?
                ]
            })

        # Class 2: Raw Chunk (The Details)
        if not self.client.schema.exists("RawChunk"):
            self.client.schema.create_class({
                "class": "RawChunk",
                "vectorizer": "text2vec-openai",
                "properties": [
                    {"name": "content", "dataType": ["text"]}, # The segment
                    {"name": "doc_id", "dataType": ["text"]},  # Link to Note
                    {"name": "user_id", "dataType": ["int"]},
                    {"name": "chunk_index", "dataType": ["int"]}
                ]
            })

    def ingest_document(
        self, 
        text: str, 
        summary: str, 
        metadata: Dict[str, Any], 
        store_raw: bool = True
    ):
        """
        Master Ingestion Method.
        Saves the Atomic Note and optionally the Raw Chunks.
        """
        # Generate a stable ID for linking
        doc_id = hashlib.md5((metadata['source_url'] + str(metadata['user_id'])).encode()).hexdigest()
        
        # 1. Ingest Atomic Note
        self.client.data_object.create(
            data_object={
                "content": summary,
                "source_url": metadata['source_url'],
                "title": metadata.get('title', 'Untitled'),
                "user_id": metadata['user_id'],
                "scope": metadata['scope'],
                "doc_id": doc_id,
                "has_raw": store_raw
            },
            class_name="AtomicNote"
        )
        print(f"   💾 Saved Atomic Note: {metadata.get('title')}")

        # 2. Ingest Raw Chunks (If enabled)
        if store_raw:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunks = text_splitter.split_text(text)
            
            with self.client.batch as batch:
                batch.batch_size = 100
                for idx, chunk in enumerate(chunks):
                    batch.add_data_object(
                        data_object={
                            "content": chunk,
                            "doc_id": doc_id,
                            "user_id": metadata['user_id'],
                            "chunk_index": idx
                        },
                        class_name="RawChunk"
                    )
            print(f"   💾 Saved {len(chunks)} Raw Chunks.")
    
    def search(self, query: str, user_id: int, k: int = 4) -> List[Dict]:
        """
        Multi-Layer Search Strategy:
        1. Search Atomic Notes (High-level concepts).
        2. Search Raw Chunks (Specific details).
        3. Merge results.
        """
        results = []
        
        # --- Layer 1: Search Atomic Notes (The Concept) ---
        # Look for notes in Private (user_id) AND Global (0)
        note_response = (
            self.client.query
            .get("AtomicNote", ["content", "title", "source_url", "doc_id", "scope", "disciplines"])
            .with_hybrid(query=query, alpha=0.5) # Balanced Keyword/Vector
            .with_where({
                "operator": "Or",
                "operands": [
                    {"path": ["user_id"], "operator": "Equal", "valueInt": user_id},
                    {"path": ["user_id"], "operator": "Equal", "valueInt": 0}
                ]
            })
            .with_limit(k)
            .with_additional(["score"])
            .do()
        )

        found_notes = note_response.get('data', {}).get('Get', {}).get('AtomicNote', [])
        
        # Track doc_ids to fetch specific chunks later
        target_doc_ids = []

        for note in found_notes:
            results.append({
                "type": "note",
                "content": f"**NOTE: {note['title']}**\n{note['content']}",
                "metadata": {
                    "source": note['source_url'],
                    "title": note['title'],
                    "disciplines": note.get('disciplines', [])
                },
                "score": note['_additional']['score']
            })
            target_doc_ids.append(note['doc_id'])

        # --- Layer 2: Drill-Down Search (The Details) ---
        # Search specifically within the RawChunks linked to the notes.
        # This ensures getting details RELEVANT to the high-level concepts found.
        if target_doc_ids:
            chunk_response = (
                self.client.query
                .get("RawChunk", ["content", "doc_id"])
                .with_hybrid(query=query, alpha=0.5)
                .with_where({
                    "operator": "And",
                    "operands": [
                        # Must belong to one of the found notes
                        {"path": ["doc_id"], "operator": "ContainsAny", "valueText": target_doc_ids},
                        # Must be accessible (Private or Global check implied by doc_id link, but safe to add)
                        {"operator": "Or", "operands": [
                            {"path": ["user_id"], "operator": "Equal", "valueInt": user_id},
                            {"path": ["user_id"], "operator": "Equal", "valueInt": 0}
                        ]}
                    ]
                })
                .with_limit(3) # Get top 3 specific details
                .with_additional(["score"])
                .do()
            )
            
            found_chunks = chunk_response.get('data', {}).get('Get', {}).get('RawChunk', [])
            
            for chunk in found_chunks:
                results.append({
                    "type": "chunk",
                    "content": f"__Detail (Citation)__:\n{chunk['content']}",
                    "metadata": {"source": "Raw Detail"},
                    "score": chunk['_additional']['score']
                })

        return results
    
rag_service = RAGService()