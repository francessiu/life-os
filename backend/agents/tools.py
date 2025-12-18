import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import Tool

from backend.agents.tools.code_execution import PythonSandboxTool

class AgentTools:
    @staticmethod
    def get_web_search_tool():
        """
        Returns a configured Web Search tool (Tavily).
        """
        # Use Tavily for RAG fallbacks
        search = TavilySearchResults(max_results=10)
        
        return Tool(
            name="web_search",
            description="Search the web for current events or missing information.",
            func=search.invoke
        )
        
    @staticmethod
    def get_code_interpreter_tool():
        return PythonSandboxTool()