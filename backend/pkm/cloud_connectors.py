import os
import httpx
from typing import List, Dict, Optional
from langchain_community.document_loaders import GoogleDriveLoader
from langchain_core.documents import Document

# TODO: Requires Google Cloud credentials and user authorization to run.

class PKMConnector:
    
    # --- Google Drive ---
    @staticmethod
    def load_google_drive(folder_id: str, credentials_path: str = "./credentials.json") -> List[Document]:
        """
        Loads documents from a Google Drive folder using Service Account or User Credentials.
        Note: This is synchronous/blocking IO, so run it via asyncio.to_thread()
        """
        try:
            loader = GoogleDriveLoader(
                folder_id=folder_id,
                credentials_path=credentials_path,
                token_path="./token.json", # Optional: stores user token
                recursive=True
            )
            # Returns a list of LangChain Document objects
            return loader.load()
        except Exception as e:
            print(f"Google Drive Error: {e}")
            return []
        
    # With direct API
    @staticmethod
    async def fetch_google_drive_files(access_token: str) -> List[Dict]:
        """
        Lists files from Google Drive using the REST API v3.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        # Query: Not trashed, and is a document/pdf/text (MIME type filtering)
        # Exclude folders (application/vnd.google-apps.folder)
        params = {
            "q": "trashed = false and mimeType != 'application/vnd.google-apps.folder'",
            "fields": "files(id, name, mimeType, exportLinks)",
            "pageSize": 50 
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://www.googleapis.com/drive/v3/files", headers=headers, params=params)
            
            if resp.status_code != 200:
                print(f"Google Drive List Error: {resp.text}")
                return []
            
            files = []
            for item in resp.json().get('files', []):
                # Google Docs require 'export' (conversion), PDFs require 'alt=media' (download)
                download_url = ""
                is_native_doc = "application/vnd.google-apps" in item['mimeType']
                
                if is_native_doc:
                    # Export Google Docs as PDF or Text
                    download_url = f"https://www.googleapis.com/drive/v3/files/{item['id']}/export?mimeType=application/pdf"
                else:
                    # Download binary files (PDF, Docx uploaded to drive)
                    download_url = f"https://www.googleapis.com/drive/v3/files/{item['id']}?alt=media"
                
                files.append({
                    "id": item["id"],
                    "name": item["name"],
                    "download_url": download_url,
                    "is_native": is_native_doc
                })
            return files
        
    @staticmethod
    async def download_google_content(url: str, access_token: str) -> Optional[bytes]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.content
            print(f"Google Download Error: {resp.status_code}")
            return None

    # --- OneDrive ---
    @staticmethod
    async def fetch_onedrive_files(access_token: str) -> List[Dict]:
        """
        Fetches file metadata from OneDrive Root.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"OneDrive List Error: {resp.status_code} - {resp.text}")
                return []
            
            data = resp.json()
            files = []
            
            # Filter for actual files (skip folders for now)
            for item in data.get('value', []):
                if 'file' in item and '@microsoft.graph.downloadUrl' in item:
                    files.append({
                        "id": item["id"],
                        "name": item["name"],
                        "download_url": item["@microsoft.graph.downloadUrl"]
                    })
            return files

    @staticmethod
    async def download_onedrive_content(url: str) -> Optional[str]:
        """ Downloads binary content from the pre-authenticated Graph URL. """
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.content
            return None