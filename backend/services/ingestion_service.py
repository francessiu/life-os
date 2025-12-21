import asyncio
from typing import Dict, Any

from backend.services.atomic_service import atomic_service
from backend.pkm.rag_service import rag_service

class IngestionService:
    async def process_and_ingest(
        self, 
        raw_text: str, 
        metadata: Dict[str, Any], 
        store_raw: bool = True
    ):
        """
        Master Pipeline:
        1. Analyzes raw text to create an Atomic Note (Title, Essence, Tags).
        2. Formats it into the specific Markdown structure.
        3. Ingests both the Note (for summary search) and Raw Chunks (for citation) into Weaviate.
        """
        source_url = metadata.get("source_url", "unknown")
        print(f"⚙️ Ingestion Pipeline: Processing {source_url}...")

        # 1. Generate Structure (AI Analysis)
        # We delegate the "thinking" to the AtomicService
        note_obj = await atomic_service.generate_note(raw_text, source_url)
        
        # 2. Format Content
        formatted_summary = atomic_service.format_as_markdown(note_obj)
        
        # 3. Update Metadata with AI Insights
        # We enhance the basic metadata with the AI-generated Title and Keywords
        enriched_metadata = metadata.copy()
        enriched_metadata["title"] = note_obj.title
        enriched_metadata["keywords"] = note_obj.keywords  # Useful for future filtering
        
        print(f" 🧠 AI Title Generated: '{note_obj.title}'")

        # 4. Push to Database (RAG)
        # We run this in a thread to avoid blocking the asyncio loop with network I/O
        await asyncio.to_thread(
            rag_service.ingest_document,
            text=raw_text,                # The Raw Content (Chunks)
            summary=formatted_summary,    # The Atomic Note (Summary)
            metadata=enriched_metadata,
            store_raw=store_raw
        )
        
        return note_obj

# Singleton
ingestion_service = IngestionService()