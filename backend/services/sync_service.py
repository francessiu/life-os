from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from backend.db.session import async_session_maker
from backend.db.models import User, OAuthAccount
from backend.pkm.connectors import PKMConnector
from backend.pkm.rag_service import rag_service

scheduler = AsyncIOScheduler()

async def sync_all_users():
    """
    Background Task: Loops through users and syncs their cloud files.
    """
    print("🔄 Starting Cloud Sync...")
    async with async_session_maker() as db:
        # 1. Find users with OAuth credentials
        result = await db.execute(select(OAuthAccount))
        accounts = result.scalars().all()
        
        for account in accounts:
            print(f"Syncing for User {account.user_id} ({account.oauth_name})...")
            
            try:
                if account.oauth_name == "google":
                    # Note: Real implementation needs to swap OAuth Token for GoogleDriveLoader credentials
                    # This is complex because GoogleDriveLoader expects a file path usually.
                    # For MVP, skip full auto-sync for Google without Service Account.
                    pass 
                    
                elif account.oauth_name == "microsoft":
                    files = await PKMConnector.fetch_onedrive_files(account.access_token)
                    for file in files:
                        content = await PKMConnector.download_onedrive_content(file['download_url'])
                        if content:
                            rag_service.ingest_text(
                                text=content, 
                                source=f"OneDrive: {file['name']}", 
                                user_id=account.user_id
                            )
            except Exception as e:
                print(f"Failed to sync user {account.user_id}: {e}")
