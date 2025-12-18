from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.session import get_async_session
from backend.db.models import User, KnowledgeSource, SourceScope
from backend.auth.users import current_active_user
from backend.services.watcher_service import run_watcher_cycle
from backend.services.crawler_service import crawler
from backend.pkm.rag_service import rag_service

router = APIRouter()

class WatchRequest(BaseModel):
    url: str
    is_global: bool = False
    frequency_hours: int = 24
    crawl_depth: int = 1 # 1 = Single Page, 10 = Deep Crawl

async def crawl_and_ingest_source(source_id: int):
    """
    Self-contained task that runs in the background.
    Opens its own DB session to avoid 'Session Closed' errors.
    """
    print(f"🚀 [Background] Starting immediate crawl for Source ID {source_id}")
    
    from backend.db.session import async_session_maker
    async with async_session_maker() as db:
        # 1. Fetch Source
        result = await db.execute(select(KnowledgeSource).where(KnowledgeSource.id == source_id))
        source = result.scalars().first()
        
        if not source:
            print(f"❌ Source {source_id} not found during background task.")
            return

        try:
            # 2. Execute Crawl (Calls Firecrawl)
            # Decide: Single URL or Domain Spider based on user input (stored in source)
            # For this example, we assume single page for simplicity, or use source.url
            data = await crawler.crawl_url(source.url)
            
            if data and data.get('content'):
                print(f"   ✅ Content fetched. Ingesting...")
                
                # 3. Ingest to RAG
                target_user_id = source.user_id if source.scope == SourceScope.PRIVATE else 0
                
                # Note: Ingest is CPU bound (embedding), run in thread
                import asyncio
                await asyncio.to_thread(
                    rag_service.ingest_text,
                    text=data['content'],
                    source=f"Web: {source.url}",
                    user_id=target_user_id,
                    metadata={
                        "title": data.get('title'),
                        "scope": source.scope.value
                    }
                )
                
                # 4. Update Source Status
                source.last_crawled_at = datetime.utcnow()
                source.title = data.get('title', source.title)
                source.error_count = 0
                
            else:
                print("   ⚠️ Crawl returned empty content.")
                source.error_count += 1
                
        except Exception as e:
            print(f"   ❌ Crawl Failed: {e}")
            source.error_count += 1
            source.last_error = str(e)
        
        # 5. Commit Updates
        db.add(source)
        await db.commit()
    
    print(f"🏁 [Background] Task finished for Source {source_id}")

@router.post("/watch")
async def add_watch_source(
    req: WatchRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Adds a URL to the Background Watcher and triggers a crawl."""
    # Security: Only Superusers should create GLOBAL sources
    if req.is_global and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can add to Global Knowledge Base.")

    scope = SourceScope.GLOBAL if req.is_global else SourceScope.PRIVATE

    # Check for duplicate
    existing = await db.execute(
        select(KnowledgeSource).where(
            KnowledgeSource.url == req.url,
            KnowledgeSource.user_id == (None if req.is_global else user.id)
        )
    )
    if existing.scalars().first():
        return {"message": "Source is already being watched."}

    # Create DB Record
    new_source = KnowledgeSource(
        user_id=None if req.is_global else user.id,
        url=req.url,
        scope=scope,
        update_frequency_hours=req.frequency_hours,
        last_crawled_at=None # Will trigger immediate crawl by watcher
    )
    
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    print(f" 🚀 Triggering instant crawl for {req.url}")
    background_tasks.add_task(crawl_and_ingest_source, new_source.id)
    
    return {"status": "queued", "scope": scope, "message": "Crawling started in background", "id": new_source.id}

@router.post("/force-run")
async def force_watcher_run(
    user: User = Depends(current_active_user)
):
    if not user.is_superuser:
         raise HTTPException(status_code=403)
    await run_watcher_cycle()
    return {"status": "Watcher cycle started"}