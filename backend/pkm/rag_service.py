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
        
        # Initialize Vector DB (Chroma)
        self.vector_db = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embedding_function
        )

    def ingest_text(self, text: str, source: str):
        """
        Takes raw text (from PDF/Web), chunks it, and saves to Vector DB.
        """
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.create_documents([text], metadatas=[{"source": source}])
        
        self.vector_db.add_documents(chunks)
        return len(chunks)

    def search(self, query: str, k: int = 3):
        """
        Retrieves the top k most relevant text chunks for a query.
        """
        results = self.vector_db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]