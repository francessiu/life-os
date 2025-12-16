import re
import ast
import hashlib
import json
from typing import List, Dict
from datetime import date
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.tools import SerperDevTool
from functools import lru_cache

from backend.agents.llm_factory import LLMFactory
from backend.agents.tools import AgentTools
from backend.pkm.rag_service import RAGService
from backend.agents.presets import AGENT_MODES

class AIAgent:
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.rag = RAGService()
        self.web_search_tool = SerperDevTool() # TODO: Get SERPER_API_KEY and set it in environment

    def _parse_llm_json(self, content: str) -> List[Dict]:
        """
        Helper to parse JSON responses from LLMs.
        """
        try:
            if "```" in content:
                content = content.split("```")[1]
                content = re.sub(r'^\w+\n', '', content.strip())

            return json.loads(content.strip())
            
        # Fallback: Try to return a simple list of strings wrapped in dicts
        except Exception as e:
            print(f"JSON Parsing failed: {e}. Content: {content}")
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return [{"title": line, "estimated_days": 7} for line in lines]
        
    def generate_subgoals(self, goal_text: str, deadline: date, days_per_week: int) -> List[Dict]:
        """
        Breaks Goal -> SubGoals (Milestones).
        """
        # Calculate context for the AI
        today = date.today()
        time_context = ""
        if deadline:
            days_remaining = (deadline - today).days
            time_context = f"DEADLINE: {deadline} ({days_remaining} days remaining)."
        else:
            time_context = "NO HARD DEADLINE. Plan for a reasonable pace."

        system_prompt = f"""
        You are an expert Project Manager and Productivity Strategist.
        
        GOAL: "{goal_text}"
        CONTEXT: {time_context}
        CONSTRAINTS: The user works on this {days_per_week} days per week.
        
        Task:
        1. Break this goal into 3-6 sequential Milestones (Sub-goals).
        2. Estimate the number of "Work Sessions" (days) required for each milestone.
        3. Ensure the plan fits within the deadline (if provided).
        
        Return ONLY a raw JSON list of objects. Do not write markdown.
        Format:
        [
            {{"title": "Milestone 1 Name", "estimated_sessions": 5, "description": "Brief outcome description"}},
            {{"title": "Milestone 2 Name", "estimated_sessions": 3, "description": "..."}}
        ]
        """
        
        # Create chain using the factory
        chain = self.llm_factory.create_generation_chain(system_prompt)
        
        # Invoke (We pass an empty input dict because all info is in the system prompt formatted above)
        # Or cleaner: Pass variables into invoke if you use PromptTemplate params.
        # Here we simple inject variables into string for simplicity.
        response = chain.invoke({"input": "Generate Plan"}) 
        
        return self._parse_llm_json(response)
    
    def replan_week(self, failed_tasks: List[str]) -> List[Dict]:
        """
        Breaks failed tasks into Micro-Tasks.
        """
        task_list_str = ", ".join(failed_tasks)
        
        system_prompt = """
        You are a supportive Productivity Coach.
        The user FAILED to complete the following tasks last week:
        
        FAILED TASKS: {failed_tasks}
        
        Diagnosis: These tasks were likely too vague or difficult.
        
        Task:
        1. Break EACH failed task down into 2-3 atomic, easy "Micro-Tasks".
        2. Assign a difficulty rating (1=Trivial, 5=Hard).
        
        Return ONLY a raw JSON list of objects.
        Format:
        [
            {{"description": "Draft just the first paragraph", "difficulty": 1, "parent_task": "Write Essay"}},
            {{"description": "Find 3 sources", "difficulty": 2, "parent_task": "Research"}}
        ]
        """
        
        # Use PromptTemplate explicitly here to inject variable safely
        prompt = PromptTemplate.from_template(system_prompt)
        
        # We need a chain that goes Prompt -> LLM -> String
        llm = self.llm_factory._create_llm("gpt-4o", temperature=0.5)
        chain = prompt | llm
        
        response = chain.invoke({"failed_tasks": task_list_str})
        
        return self._parse_llm_json(response.content)
    
    def _is_context_relevant(self, rag_results: list, threshold: float = 0.5) -> bool:
        """
        Checks if the retrieved documents are actually relevant to the query based on the Vector Distance Score.
        
        Note: For Euclidean Distance (L2), LOWER is better. 
        Adjust logic if using Cosine Similarity (where HIGHER is better).
        """
        if not rag_results:
            return False
            
        # Get the score of the BEST match (the first one)
        top_score = rag_results[0]["score"]
        
        # L2 Distance: If distance is large (e.g. > 0.5), it's a bad match.
        print(f"Top RAG Match Score: {top_score}")
        
        return top_score < threshold
    
    async def query_with_context(self, query: str, user_id: int, mode: str = "productivity", overrides: dict = None) -> str:
        # --- Load Base Config from Presets ---
        # This gets the default model/prompt for "productivity", "academic", etc.
        base_config = AGENT_MODES.get(mode, AGENT_MODES["productivity"])
        final_config = base_config.copy()
        
        # --- Apply User Overrides ---         
        if overrides:
            if overrides.get("tone"):
                # Append tone instruction to system prompt
                final_config.system_prompt += f" Adopt a {overrides['tone']} tone."
            if overrides.get("refinement_level"):
                final_config.refinement_level = overrides["refinement_level"]
        
        # --- Retrieve Documents ---
        # (Sync or Async depending on Vector DB driver)
        # Assuming rag.search is blocking, run in thread pool if needed, 
        # but Chroma is usually fast enough for MVP.
        rag_results = self.rag.search(query, user_id=user_id, k=4)
        
        source_label = "Local Knowledge Base"
        context_text = ""
        
        # Relevance check & fallback
        if self._is_context_relevant(rag_results):
            context_text = "\n\n".join([doc['content'] for doc in rag_results])
        else:
            print(f"⚠️ Low relevance. Triggering Web Search...")
            try:
                # Use arun (Async) if available, otherwise wrap run
                if hasattr(self.web_search_tool, 'arun'):
                    web_results = await self.web_search_tool.arun(query)
                else:
                    web_results = self.web_search_tool.run(query)
                
                # Combine whatever weak local context we have + Web Results
                local_text = "\n".join([doc['content'] for doc in rag_results])
                web_text = str(web_results)
                
                context_text = f"Local Context (Weak Match):\n{local_text}\n\nWeb Search Results:\n{web_text}"
                source_label = "Web Search & Weak Local Context"
            except Exception as e:
                print(f"Web search failed: {e}")
                context_text = "No relevant context found."

        # --- Generate answer using the specific agent profile ---
        chain = self.llm_factory.get_agent_chain(final_config)
        
        response = chain.invoke({
            "context": context_text,
            "question": query,
            "source_label": source_label
        })
        
        return response
    