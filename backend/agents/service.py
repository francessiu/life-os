from langchain_core.prompts import PromptTemplate
from backend.agents.llm_factory import LLMFactory
from backend.pkm.rag_service import RAGService
from functools import lru_cache
import hashlib
import ast
import re

class AIAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm("openai")
        self.rag = RAGService()

    def decompose_goal(self, goal_text: str):
        prompt = PromptTemplate.from_template(
            """
            You are an expert productivity coach.
            Goal: {goal}
            
            Break this goal down into 5 actionable, measurable steps. 
            Return ONLY a python list of strings.
            Example: ["Step 1", "Step 2"]
            """
        )
        chain = prompt | self.llm
        response = chain.invoke({"goal": goal_text})
        content = response.content.strip()

        # Safely extract and parse the list structure
        try:
            # Step 1: Clean up markdown code blocks if present
            if "```" in content:
                content = content.split("```")[1]
                # Remove optional language identifier (e.g., "python\n")
                content = re.sub(r'^\w+\n', '', content.strip())

            # 2. Safe Evaluation (Converts string "['a', 'b']" to list ['a', 'b'])
            steps = ast.literal_eval(content.strip())
            
            # Ensure it's actually a list
            if isinstance(steps, list):
                return steps
            else:
                return [content] # Fallback if LLM returned a single string

        except Exception as e:
            print(f"Error parsing LLM response: {content} | Error: {e}")
            # Fallback: Split by newlines if parsing fails
            return [line.strip() for line in content.split('\n') if line.strip()]
        
            # If all else fails, raise an error
            raise ValueError("LLM response could not be parsed into a Python list.")

    @lru_cache(maxsize=100)
    def _get_cached_response(self, query_hash: str):
        return None  # In real implementation, check Redis/Dict
    
    def query_with_context(self, query: str, user_id: int):
        # 1. Create a hash of the query + user_id for caching
        query_hash = hashlib.sha256(f"{user_id}:{query}".encode()).hexdigest()
        
        # 2. Check Cache (Simple in-memory for MVP)
        if hasattr(self, "response_cache") and query_hash in self.response_cache:
            return self.response_cache[query_hash]
        
        # 3. Retrieve relevant docs
        context_docs = self.rag.search(query, user_id)
        context_text = "\n\n".join(context_docs)
        
        if not context_text:
            context_text = "No personal documents found on this topic."

        # 4. Generate Answer
        prompt = PromptTemplate.from_template(
            """
            Answer the user's question based ONLY on the context provided below.
            If the answer isn't in the context, say "I don't have that info in your database."
            
            Context:
            {context}
            
            Question: 
            {question}
            """
        )
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context_text, "question": query})
        
        # 4. Save to Cache
        if not hasattr(self, "response_cache"): self.response_cache = {}
        self.response_cache[query_hash] = response.content
        
        return response.content