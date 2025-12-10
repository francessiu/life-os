from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.core.config import settings
import os

class RAGService:
    def __init__(self):
        # OpenAI embeddings for high-quality search
        self.embedding_function = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.persist_dir = settings.PERSIST_DIRECTORY
        
    def _get_user_db(self, user_id: int):
        """Initializes/loads the Chroma DB instance scoped to a specific user."""
        user_db_path = os.path.join(self.persist_dir, f"user_{user_id}")
        os.makedirs(user_db_path, exist_ok=True)
        
        return Chroma(
            persist_directory=user_db_path,
            embedding_function=self.embedding_function
        )

    def ingest_text(self, text: str, source: str, user_id: int):
        """
        Takes raw text (from PDF/Web), chunks it, and saves to Vector DB for a specific user.
        """
        user_db = self._get_user_db(user_id)
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.create_documents([text], metadatas=[{"source": source, "user_id": user_id}])
        
        user_db.add_documents(chunks)
        user_db.persist()
        return len(chunks)

    def search(self, query: str, user_id: int, k: int = 3):
        """
        Retrieves the top k most relevant text chunks from the specified user's store for a query.
        """
        user_db = self._get_user_db(user_id)
        results = user_db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]