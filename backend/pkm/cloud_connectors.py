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

    # --- OneDrive ---
    @staticmethod
    async def fetch_onedrive_files(access_token: str) -> List[Dict]:
        """
        Fetches file metadata from OneDrive Root.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://graph.microsoft.com/v1.0/me/drive/root/children", headers=headers)
            if resp.status_code != 200:
                print(f"OneDrive API Error: {resp.text}")
                return []
            
            # Filter for downloadable files
            return [
                {
                    "name": item["name"], 
                    "download_url": item["@microsoft.graph.downloadUrl"]
                }
                for item in resp.json().get('value', []) 
                if '@microsoft.graph.downloadUrl' in item
            ]

    @staticmethod
    async def download_onedrive_content(url: str) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                # Return text content (simplified for MVP)
                # Ideally, use 'parsers.py' logic here for PDF/Docx bytes
                try:
                    return resp.content.decode('utf-8')
                except:
                    return None # Binary file handling needed in parser
            return None