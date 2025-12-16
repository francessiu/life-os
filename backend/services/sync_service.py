import asyncio
from datetime import datetime, timedelta
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_maker
from backend.db.models import User, OAuthAccount
from backend.pkm.connectors import PKMConnector
from backend.pkm.parsers import parse_file_bytes
from backend.pkm.rag_service import rag_service
from backend.core.config import settings

scheduler = AsyncIOScheduler()

# --- Helper: Authentication Token Refresh ---
async def refresh_oauth_token(db: AsyncSession, account: OAuthAccount) -> str:
    """
    Checks if token is expired. If so, uses refresh_token to get a new access_token.
    Updates DB and returns valid access_token.
    """
    # 5 minute buffer
    if account.expires_at and datetime.utcfromtimestamp(account.expires_at) > datetime.utcnow() + timedelta(minutes=5):
        return account.access_token

    print(f"🔄 Refreshing Token for {account.oauth_name} (User {account.user_id})")
    
    new_token = None
    new_expiry = None
    
    async with httpx.AsyncClient() as client:
        try:
            if account.oauth_name == "google":
                resp = await client.post("https://oauth2.googleapis.com/token", data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": account.refresh_token,
                    "grant_type": "refresh_token"
                })
                data = resp.json()
                new_token = data.get("access_token")
                new_expiry = int(datetime.utcnow().timestamp()) + data.get("expires_in", 3600)
                
            elif account.oauth_name == "microsoft":
                resp = await client.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "refresh_token": account.refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "Files.Read.All offline_access"
                })
                data = resp.json()
                new_token = data.get("access_token")
                new_expiry = int(datetime.utcnow().timestamp()) + data.get("expires_in", 3600)

            if new_token:
                # Update DB
                account.access_token = new_token
                account.expires_at = new_expiry
                db.add(account)
                await db.commit()
                return new_token
            
        except Exception as e:
            print(f"Token Refresh Failed: {e}")
            
    return account.access_token # Return old token as fallback (likely will fail)

# --- Core Sync Logic ---
async def process_file_sync(user_id: int, files_meta: list, access_token: str, provider: str):
    """
    Iterates files, downloads content, extracts text, and ingests to RAG.
    """
    print(f" ⏳ Processing {len(files_meta)} files from {provider}...")

    for meta in files_meta:
        try:
            content_bytes = None
            
            # 1. Download Content based on Provider
            if provider == "GoogleDrive":
                content_bytes = await PKMConnector.download_google_content(
                    meta['download_url'], 
                    access_token
                )
            elif provider == "OneDrive":
                content_bytes = await PKMConnector.download_onedrive_content(
                    meta['download_url']
                )

            # 2. Parse & Ingest
            if content_bytes:
                # Extract text from PDF/Docx/Txt bytes
                text = parse_file_bytes(content_bytes, meta['name'])
                
                if text:
                    # Run RAG ingestion in a thread (CPU bound) to avoid blocking async loop
                    await asyncio.to_thread(
                        rag_service.ingest_text,
                        text=text,
                        source=f"{provider}: {meta['name']}",
                        user_id=user_id
                    )
                    print(f" ✅ Indexed: {meta['name']}")
                else:
                    print(f" ⚠️ Empty/Unsupported: {meta['name']}")
            else:
                print(f" ❌ Download Failed: {meta['name']}")

        except Exception as e:
            print(f" ❌ Error processing {meta['name']}: {str(e)}")
            
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
                # 1. Ensure Token is Valid
                valid_token = await refresh_oauth_token(db, account)
                
                # 2. Fetch Metadata & Delegate Processing
                if account.oauth_name == "google":
                    files = await PKMConnector.fetch_google_drive_files(valid_token)
                    await process_file_sync(account.user_id, files, valid_token, "GoogleDrive")

                elif account.oauth_name == "microsoft":
                    files = await PKMConnector.fetch_onedrive_files(valid_token)
                    await process_file_sync(account.user_id, files, valid_token, "OneDrive")

            except Exception as e:
                print(f"❌ Sync Error for User {account.user_id}: {e}")
