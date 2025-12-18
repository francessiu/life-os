import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_maker
from backend.db.models import KnowledgeSource, SourceScope
from backend.services.crawler_service import crawler
from backend.pkm.rag_service import rag_service

async def run_watcher_cycle():
    """Cron Task: Checks for sources that need updating."""
    print("🔭 Watcher: Scanning for stale sources...")
    
    async with async_session_maker() as db:
        # 1. Find Active Sources where (Now - LastCrawled) > Frequency
        threshold_time = datetime.utcnow() - timedelta(hours=24)
        
        stmt = select(KnowledgeSource).where(
            and_(
                KnowledgeSource.is_active == True,
                or_(
                    KnowledgeSource.last_crawled_at == None,
                    KnowledgeSource.last_crawled_at < threshold_time
                )
            )
        )
        
        result = await db.execute(stmt)
        sources_to_update = result.scalars().all()
        
        print(f" ↳ Found {len(sources_to_update)} sources needing update.")
        
        for source in sources_to_update:
            print(f" ⟳ Updating Source: {source.url} (Scope: {source.scope})")
            
            try:
                # 2. Perform Crawl
                data = await crawler.crawl_url(source.url)
                
                if data and data['content']:
                    # 3. Ingest into RAG
                    # If Scope is GLOBAL, ingest with a special 'global' user_id (e.g. 0), or handle permissions in the RAG search logic.
                    target_user_id = source.user_id if source.scope == SourceScope.PRIVATE else 0
                    
                    await asyncio.to_thread(
                        rag_service.ingest_text,
                        text=data['content'],
                        source=f"Watcher: {source.url}",
                        user_id=target_user_id,
                        metadata={"scope": source.scope.value, "title": data['title']}
                    )
                    
                    # 4. Update Success State
                    source.last_crawled_at = datetime.utcnow()
                    source.error_count = 0
                    source.title = data['title']
                    
                else:
                    source.error_count += 1
            
            except Exception as e:
                print(f"   ❌ Watcher Error: {e}")
                source.error_count += 1
                source.last_error = str(e)
            
            # Commit per source to save progress
            db.add(source)
            await db.commit()