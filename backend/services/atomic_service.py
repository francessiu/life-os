import json
import tiktoken
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.core.config import settings

class AtomicNoteSchema(BaseModel):
    title: str = Field(description="A concise title for the note.")
    keywords: List[str] = Field(description="List of specific topic tags (e.g., #LLM, #Productivity).")
    disciplines: List[str] = Field(description="Broad academic or professional domains (e.g., 'Computer Science', 'Philosophy').")
    actions: List[str] = Field(default=[], description="List of action tags (e.g., @coding, @review).")
    essence: str = Field(description="A 2-5 sentence high-level abstract/summary.")
    core_idea: str = Field(description="The main body of the note. Detailed insights and arguments.")
    action_idea: Optional[str] = Field(default=None, description="Concrete next steps or projects implied by the text.")
    reference: str = Field(description="The source URL.")

class AtomicService:
    def __init__(self):
        # Use a smart model for semantic analysis
        self.llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0.1, # Low temp for strict JSON adherence
            api_key=settings.OPENAI_API_KEY
        )
        self.parser = PydanticOutputParser(pydantic_object=AtomicNoteSchema)
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        
    def _truncate_content(self, text: str, max_tokens: int = 120000) -> str:
        """Safely truncates text to fit context window."""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        print(f"⚠️ Truncating document from {len(tokens)} to {max_tokens} tokens.")
        return self.tokenizer.decode(tokens[:max_tokens])

    async def generate_note(self, raw_content: str, source_url: str) -> AtomicNoteSchema:
        """Analyzes raw text and returns a structured Atomic Note object."""
        # Prepare Content (Token Safety)
        # We leave ~8k tokens for the response and system prompt
        safe_content = self._truncate_content(raw_content, max_tokens=110000)
        
        # System Prompt
        system_prompt = """
        You are an expert Knowledge Manager. 
        Analyze the provided document and distill it into an "Atomic Note".
        
        GOALS:
        - Identify the Broad Disciplines (e.g. Economics, Physics).
        - Extract specific Keywords (Tags).
        - Synthesize the "Essence" (Abstract).
        - Detail the "Core Idea" (The Knowledge).
        - Extract "Action Items" if applicable.
        
        STRUCTURE REQUIREMENTS:
        1. Title: Clear and descriptive.
        2. Disciplines: Relevant academic or professional disciplines 
        3. Tags: Relevant keywords (#) and actions (@).
        4. Essence: A high-level abstract.
        5. Core Idea: The detailed insight.
        6. Action Idea: If the content implies a task or project, extract it.
        7. Reference: The source URL provided.
        
        Refuse to hallucinate. If the document is empty or noise, return "N/A" fields.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Source URL: {source_url}\n\nCONTENT:\n{content}\n\n{format_instructions}")
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            return await chain.ainvoke({
                "content": safe_content,
                "source_url": source_url,
                "format_instructions": self.parser.get_format_instructions()
            })
        except Exception as e:
            # Fallback for parsing errors (Auto-fix logic could go here)
            print(f"❌ Atomic Note Generation Failed: {e}")
            raise e

    def format_as_markdown(self, note: AtomicNoteSchema) -> str:
        """Renders the note for the UI/Human Reading."""
        # Format Keywords & Actions
        kw_str = " ".join([f"#{k.strip().replace('#','')}" for k in note.keywords])
        ac_str = " ".join([f"@{a.strip().replace('@','')}" for a in note.actions])
        disc_str = ", ".join(note.disciplines)

        md = f"""# {note.title}
**Disciplines:** {disc_str}
**Tags:** {kw_str} {ac_str}

## Essence
{note.essence}

## Core Idea
{note.core_idea}
"""
        if note.action_idea:
            md += f"\n## Action Idea\n{note.action_idea}\n"
            
        md += f"\n## Reference\n[{note.reference}]({note.reference})"
        
        return md
# Singleton
atomic_service = AtomicService()