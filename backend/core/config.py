import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", "./backend/db/chroma_storage")
    
settings = Settings()

print(f"Loaded Anthropic Key: {os.getenv('ANTHROPIC_API_KEY')}")