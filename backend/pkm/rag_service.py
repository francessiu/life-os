import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document

from backend.core.config import settings

class RAGService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in settings.")
        
        # OpenAI embeddings for high-quality search
        self.embedding_function = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.persist_dir = settings.PERSIST_DIRECTORY
        
    def _get_user_db(self, user_id: int):
        """
        Initializes/loads the Chroma DB instance scoped to a specific user.
        Structure: ./backend/db/chroma_storage/user_1/
        """
        user_db_path = os.path.join(self.persist_dir, f"user_{user_id}")
        os.makedirs(user_db_path, exist_ok=True)
        
        return Chroma(
            persist_directory=user_db_path,
            embedding_function=self.embedding_function,
            collection_name=f"user_{user_id}_collection"
        )

    def ingest_text(self, text: str, source: str, user_id: int):
        """
        Takes raw text (from PDF/Web), chunks it, and saves to Vector DB for a specific user.
        """
        user_db = self._get_user_db(user_id)
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        metadata = {"source": source, "user_id": user_id}
        chunks = text_splitter.create_documents([text], metadatas=[metadata])
        
        user_db.add_documents(chunks)
        user_db.persist()
        return len(chunks)
    
    def search(self, query: str, user_id: int, k: int = 4):
        """
        Implements HYBRID SEARCH (Vector + Keyword).
        """
        user_db = self._get_user_db(user_id)
        
        # 1. Vector Retriever (Semantic)
        vector_retriever = user_db.as_retriever(search_kwargs={"k": k})
        
        # 2. Keyword Retriever (BM25)
        # Note: BM25 needs all docs in memory to build index. 
        # For production with millions of docs, use Weaviate/Pinecone which has Hybrid built-in.
        # For a local MVP, fetch typical docs or maintain a separate index.
        # Here is a simplified pattern:
        
        # Get all docs (Warning: Expensive for large DBs)
        # In a real app, persist the BM25 index separately.
        all_docs = user_db.get()['documents'] 
        all_metadatas = user_db.get()['metadatas']
        doc_objects = [Document(page_content=t, metadata=m) for t, m in zip(all_docs, all_metadatas)]
        
        if not doc_objects:
            return []

        bm25_retriever = BM25Retriever.from_documents(doc_objects)
        bm25_retriever.k = k

        # 3. Ensemble (Combine Results)
        # Weights: 0.5 Vector, 0.5 Keyword
        ensemble_retriever = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.5, 0.5]
        )
        
        results = ensemble_retriever.invoke(query)
        
        # Standardise Output with Scores (Ensemble doesn't always give raw scores easily, so normalise)
        return [{"content": doc.page_content, "metadata": doc.metadata, "score": 0.9} for doc in results]
    
rag_service = RAGService()