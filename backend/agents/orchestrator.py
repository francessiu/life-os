import json
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from backend.core.config import settings
from backend.agents.presets import AGENT_MODES

class AgentOrchestrator:
    def __init__(self):
        # Use a fast, cheap model for routing (e.g., GPT-3.5-Turbo or GPT-4o-mini)
        self.router_llm = ChatOpenAI(
            model="gpt-3.5-turbo", 
            temperature=0, 
            api_key=settings.OPENAI_API_KEY
        )
        
        # Dynamically build list of available modes from your presets
        self.available_modes = list(AGENT_MODES.keys()) # e.g. ['productivity', 'academic', 'casual']

    async def route_query(self, query: str) -> str:
        """
        Analyzes the query and returns the best matching AGENT_MODE key.
        """
        system_prompt = f"""
        You are the Master Router for LifeOS.
        Your job is to select the best specialised AI Agent for a given user query.
        
        AVAILABLE AGENTS:
        - academic: For research, complex concepts, and citing sources.
        - coder: For writing software.
        - analyst: For writing analysis.
        - research: For complex questions requiring deep investigation, gathering data from multiple sources, or creating comprehensive reports. (e.g. "Research the history of...", "Compare X and Y in depth").
        - casual: For chatting, emotional support, life advice, and fun.
        - creative: For developing idea, brainstorming, and creativity.
        
        INSTRUCTIONS:
        1. Analyze the USER QUERY complexity.
        2. If it requires NEW information from the web to be comprehensive -> Select 'research'.
        3. Otherwise select the single best match from the list: {self.available_modes}.
        3. If unsure, default to 'productivity'.
        4. Return ONLY the key string (e.g., "academic"). Do not add punctuation.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{query}")
        ])
        
        chain = prompt | self.router_llm | StrOutputParser()
        
        try:
            mode = await chain.ainvoke({"query": query})
            mode = mode.strip().lower()
            
            if mode in self.available_modes:
                return mode
            return "productivity" # Default fallback
            
        except Exception as e:
            print(f"Routing failed: {e}")
            return "productivity"