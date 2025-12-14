import os
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from backend.core.config import settings
from backend.schemas import AgentConfig

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
    
    def get_agent_chain(self, config: AgentConfig):
        """
        Dynamically builds a chain based on the Pydantic Config.
        """
        # 1. Instantiate the specific model requested (The "Vending Machine" logic)
        llm = self._create_llm(config.model, config.temperature)
        
        # 2. Prompt with SOURCE_LABEL variable
        prompt = ChatPromptTemplate.from_messages([
            ("system", config.system_prompt),
            ("user", 
             """
             Information Source: {source_label}
             
             Context:
             {context}
             
             Question: 
             {question}
             """)
        ])
        
        # 3. Build Chain
        chain = (
            {
                "context": RunnablePassthrough(), 
                "question": RunnablePassthrough(),
                "source_label": RunnablePassthrough() # Passed from Service
            }
            | prompt 
            | llm 
            | StrOutputParser()
        )
        
        return chain