import io
from typing import Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
from fastapi import UploadFile

from backend.services.vision_service import vision_service

async def parse_file_bytes(content: bytes, filename: str) -> Optional[str]:
    """
    Core Logic: Extracts text from raw bytes based on extension, including using AI vision for images. 
    Used by both API Uploads and Cloud Sync.
    """
    file_ext = filename.split('.')[-1].lower()
    text = ""
    
    try:
        if file_ext in ["jpg", "jpeg", "png", "webp"]:
            text = await vision_service.analyze_image(content, filename)
            
        elif file_ext == "pdf":
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif file_ext in ["docx", "doc"]:
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif file_ext in ["txt", "md", "csv", "json"]:
            # Try utf-8, fallback to latin-1 for legacy files
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
                
        else:
            # print(f"Unsupported file type: {file_ext}")
            return None 

    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

    return text.strip()

async def extract_text_from_upload(file: UploadFile) -> Optional[str]:
    """
    Wrapper for FastAPI UploadFile objects (Local Uploads).
    """
    content = await file.read()
    await file.seek(0) # Reset cursor for safety
    return parse_file_bytes(content, file.filename)