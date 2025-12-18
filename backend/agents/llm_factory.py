import os
from typing import Any, List, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent

from backend.core.config import settings
from backend.schemas import AgentConfig

class LLMFactory:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.google_api_key = settings.GOOGLE_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

    def _create_llm(self, provider: str, model_name: str, temperature: float) -> Any:
        try:
            if provider == "openai":
                return ChatOpenAI(model=model_name, temperature=temperature, api_key=settings.OPENAI_API_KEY)
            
            elif provider == "anthropic":
                return ChatAnthropic(model=model_name, temperature=temperature, api_key=settings.ANTHROPIC_API_KEY)
            
            elif provider == "google":
                return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, api_key=settings.GOOGLE_API_KEY)
            
            else:
                # Fallback to a safe default if provider is unknown
                print(f"⚠️ Unknown provider '{provider}'. Falling back to OpenAI.")
                return ChatOpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)

        except Exception as e:
            # Ultimate fallback
            print(f"❌ Failed to create LLM for {provider}/{model_name}: {e}")
            return ChatOpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)
    
    def get_agent_chain(self, config: AgentConfig):
        """
        Dynamically builds a chain based on the Pydantic Config.
        """
        # 1. Instantiate the specific model requested
        llm = self._create_llm(provider=config.provider, model_name=config.model, temperature=config.temperature)
        
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
    
    def get_agent_runner(self, config: AgentConfig, tools: List[BaseTool]) -> AgentExecutor:
        """
        Returns a Runnable that supports Tool Calling.
        Replaces 'get_agent_chain' for advanced agents.
        """
        llm = self._create_llm(config.provider, config.model, config.temperature)

        prompt = ChatPromptTemplate.from_messages([
            ("system", config.system_prompt),
            ("user", 
             """
             Information Source: {source_label}
             
             Context:
             {context}
             
             Question: 
             {question}
             """),
            ("placeholder", "{agent_scratchpad}"), # Required for tool outputs
        ])
        
        # Create the Agent (The Brain that decides which tool to call)
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # Create the Executor (The Runtime that actually runs the tools and loops back)
        executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, # Logs thoughts to console
            handle_parsing_errors=True # Auto-retry if LLM makes a typo in tool call
        )
        
        return executor