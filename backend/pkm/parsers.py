import io
from typing import Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
from fastapi import UploadFile

async def extract_text_from_upload(file: UploadFile) -> Optional[str]:
    """
    Detects file type and extracts text content.
    """
    content = await file.read()
    file_ext = file.filename.split('.')[-1].lower()
    
    text = ""

    try:
        if file_ext == "pdf":
            # Process PDF
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        elif file_ext in ["docx", "doc"]:
            # Process Word Doc
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            for para in doc.paragraphs:
                text += para.text + "\n"

        elif file_ext in ["txt", "md", "csv"]:
            # Process Plain Text
            text = content.decode("utf-8")
            
        else:
            return None # Unsupported type

    except Exception as e:
        print(f"Error parsing {file.filename}: {e}")
        return None
        
    # Reset cursor for safety if needed elsewhere
    await file.seek(0)
    
    return text.strip()