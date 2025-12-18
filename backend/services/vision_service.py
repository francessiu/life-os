import base64
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.core.config import settings

class VisionService:
    def __init__(self):
        # We use GPT-4o for high-quality image analysis
        self.vision_model = ChatOpenAI(
            model="gpt-4o", 
            temperature=0,
            max_tokens=1000,
            api_key=settings.OPENAI_API_KEY
        )

    def _encode_image(self, image_bytes: bytes) -> str:
        """Encodes bytes to Base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')

    async def analyze_image(self, image_bytes: bytes, filename: str) -> str:
        """Generates a detailed text description of an image for RAG indexing."""
        base64_image = self._encode_image(image_bytes)
        
        prompt = f"""
        Analyze this image (Filename: {filename}). 
        Provide a detailed, descriptive summary of its contents.
        - If it is a diagram or chart, explain the data and relationships.
        - If it is a document screenshot, transcribe the key text.
        - If it is a photo, describe the objects and context.
        
        Output ONLY the description.
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )

        try:
            response = await self.vision_model.ainvoke([message])
            return response.content
        except Exception as e:
            print(f"Vision Analysis Failed: {e}")
            return f"[Image Analysis Failed for {filename}]"

# Singleton
vision_service = VisionService()