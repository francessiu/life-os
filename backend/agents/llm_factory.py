from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.core.config import settings

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = "openai"):
        if provider == "openai":
            return ChatOpenAI(
                model="gpt-4o", 
                temperature=0.7, 
                api_key=settings.OPENAI_API_KEY
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-pro", 
                temperature=0.7, 
                google_api_key=settings.GOOGLE_API_KEY
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model="claude-3-5-sonnet", 
                temperature=0.5, 
                api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")