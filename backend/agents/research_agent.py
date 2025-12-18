import asyncio
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.schemas import ResearchPlan, AgentConfig
from backend.agents.llm_factory import LLMFactory
from backend.agents.tools import AgentTools
from backend.pkm.rag_service import rag_service
from backend.core.config import settings

class ResearchAgent:
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.web_search_tool = AgentTools.get_web_search_tool()
        
        # Planner Configuration
        self.planner_config = AgentConfig(
            name="Research Planner",
            provider="openai",
            model="gpt-4o", # Use a smart model
            temperature=0.2, # Low temp for structured planning
            system_prompt="You are a Strategic Research Lead. Break down complex user questions into executable search strategies."
        )
        
        # Synthesizer Configuration
        self.synthesizer_config = AgentConfig(
            name="Research Synthesizer",
            provider="anthropic", # Claude 3 Opus/Sonnet is excellent for synthesis
            model="claude-3-opus-20240229",
            temperature=0.4,
            system_prompt="You are a Comprehensive Report Writer. Synthesize a vast amount of gathered information into a coherent, cited, and detailed answer."
        )

    async def run_deep_research(self, user_query: str, user_id: int) -> str:
        """
        Executes the full Deep Research Workflow:
        1. PLAN: Generate queries.
        2. EXECUTE: Parallel web search.
        3. INGEST: Save findings to User DB.
        4. SYNTHESIZE: Generate final answer.
        """
        print(f"🕵️‍♀️ Starting Deep Research for: {user_query}")

        # --- STEP 1: THE PLANNER ---
        plan = await self._generate_plan(user_query)
        print(f" 📝 Plan Generated: {len(plan.search_queries)} queries")
        print(f" Strategy: {plan.explanation}")

        # --- STEP 2: THE EXECUTOR (Parallel) ---
        # Run all search queries at once
        tasks = [self._execute_search(q) for q in plan.search_queries]
        search_results_list = await asyncio.gather(*tasks)
        
        # Flatten results (List of Lists -> Single List)
        # Normalize to a list of dicts: [{'content': '...', 'url': '...'}]
        aggregated_findings = []
        for res in search_results_list:
            if isinstance(res, list):
                aggregated_findings.extend(res)
            elif isinstance(res, str):
                aggregated_findings.append({"content": res, "url": "web_search"})

        # --- STEP 3: JUST-IN-TIME INGESTION ---
        # Ingest everything found into the Vector DB immediately.
        print(f" 💾 Ingesting {len(aggregated_findings)} snippets into PKM...")
        
        ingestion_tasks = []
        full_context_text = ""
        
        for item in aggregated_findings:
            content = item.get('content', '')
            source = item.get('url', 'Deep Research')
            
            if not content: continue
            
            full_context_text += f"Source: {source}\nContent: {content}\n\n"
            
            # Async Ingestion 
            # Wait to ensure consistency for future queries
            ingestion_tasks.append(
                asyncio.to_thread(
                    rag_service.ingest_text, 
                    text=content, 
                    source=f"DeepResearch: {source}", 
                    user_id=user_id
                )
            )
        
        await asyncio.gather(*ingestion_tasks)

        # --- STEP 4: THE SYNTHESIZER ---
        print("   🧠 Synthesizing Final Report...")
        final_answer = await self._synthesize_report(user_query, plan, full_context_text)
        
        return final_answer

    async def _generate_plan(self, query: str) -> ResearchPlan:
        """Uses LLM to generate search queries."""
        parser = PydanticOutputParser(pydantic_object=ResearchPlan)
        
        # Get runner (using strict JSON mode if provider supports it, or parsing)
        # Rely on the prompt to enforce format here
        llm = self.llm_factory._create_llm(
            self.planner_config.provider, 
            self.planner_config.model, 
            self.planner_config.temperature
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.planner_config.system_prompt),
            ("user", "User Question: {question}\n\n{format_instructions}")
        ])
        
        chain = prompt | llm | parser
        
        return await chain.ainvoke({
            "question": query,
            "format_instructions": parser.get_format_instructions()
        })

    async def _execute_search(self, query: str) -> List[Dict]:
        """Runs a single search query."""
        try:
            # Use 'arun' if available (async), else wrap sync run
            if hasattr(self.web_search_tool, 'arun'):
                return await self.web_search_tool.arun(query)
            else:
                return await asyncio.to_thread(self.web_search_tool.run, query)
        except Exception as e:
            print(f" ❌ Query failed '{query}': {e}")
            return []

    async def _synthesize_report(self, query: str, plan: ResearchPlan, context: str) -> str:
        """Generates the final answer."""
        system_prompt = f"""
        You are a Deep Research Synthesizer. 
        User Question: "{query}"
        
        Research Strategy Used: {plan.explanation}
        
        Your Goal: Write a definitive, comprehensive answer based ONLY on the provided Context.
        - Structure the answer with clear headings.
        - You MUST cite the sources provided in the context (e.g., [Source: url]).
        - If the context contradicts itself, note the conflict.
        - Be exhaustive.
        """
        
        # Create a temp config for the factory
        config = self.synthesizer_config.copy()
        config.system_prompt = system_prompt
        
        chain = self.llm_factory.get_agent_chain(config)
        
        # We pass context as 'context' variable
        return await chain.ainvoke({
            "context": context,
            "question": query, 
            "source_label": "Deep Research Aggregation"
        })