import os
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence

from backend.core.config import settings

# TODO: Connect to PostgreSQL DB in real implementation 
def fetch_user_preferences(user_id: str) -> Dict[str, Any]:
    """Retrieves mock user preferences for personalization."""
    # Mock data structure based on R2.6
    return {
        "tone": "formal",
        "refinement_level": "concise",
        "bio": "A graduate student focused on academic research.",
        "model_primary": "gpt-4o",  # High-quality model for reasoning
        "temp_primary": 0.7,
        "model_summariser": "gpt-3.5-turbo", # Faster, cheaper for summarization
        "temp_summariser": 0.1
    }

class LLMFactory:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.google_api_key = settings.GOOGLE_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

    def _create_llm(self, model_name: str, **kwargs) -> Any:
        if "gpt" in model_name:
            return ChatOpenAI(model=model_name, api_key=self.openai_api_key, **kwargs)
        elif "gemini" in model_name:
            return ChatGoogleGenerativeAI(model=model_name, api_key=self.google_api_key, **kwargs)
        elif "claude" in model_name:
            return ChatAnthropic(model=model_name, api_key=settings.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM model: {model_name}")

    def get_personalized_llm_chain(self, user_id: str) -> RunnableSequence:
        """
        Creates a LangChain sequence: Primary Model -> Summarizer Model (P2.1, R2.3).
        """
        # 1. Fetch User Preferences
        prefs = fetch_user_preferences(user_id)
        personality = prefs.get("tone", "formal")
        refinement = prefs.get("refinement_level", "detailed")
        
        # 2. Define Primary Prompt and Model
        SYSTEM_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
            ("system", 
             f"""
             You are the LifeOS assistant. 
             You combine the ruthless logic, execution strategy of a tech lead, the cultural depth of an mentor, and the deep, rigorous knowledge of a specialised academic.
             Adopt a {personality} tone. 
             User Profile Summary: {prefs.get('bio', 'N/A')}. 
             Your task is to provide a direct, constructive, comprehensive, detailed answer based on the provided context.
             """)
        ])
        
        primary_model = self._create_llm(
            model_name=prefs.get("model_primary"), 
            temperature=prefs.get("temp_primary") 
        )

        # 3. Define Summarization Prompt and Model (R2.3)
        SUMMARISER_PROMPT = ChatPromptTemplate.from_messages([
            ("system", 
             f"""
             Review the detailed response below (enclosed in triple backticks) and summarise it. 
             The requested level of refinement is '{refinement}'. Be as brief or detailed as requested.
             
             Detailed response:
             ```
             {{response}}
             ```
             """)
        ])

        summariser_model = self._create_llm(model_name=prefs.get('model_summariser'), temperature=prefs.get("temp_summmariser"))

        # 4. Define Chain: Primary -> Summariser
        chain = (
            SYSTEM_PROMPT_TEMPLATE 
            | primary_model 
            | SUMMARISER_PROMPT 
            | summariser_model
        )
        
        return chain