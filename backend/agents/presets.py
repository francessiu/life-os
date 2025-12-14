from backend.schemas import AgentConfig

AGENT_MODES = {
    "productivity": AgentConfig(
        name="Productivity Coach",
        model="gpt-4o",
        temperature=0.3, # Low temp for actionable, strict advice
        system_prompt="You are a ruthless productivity coach. Focus on action items, deadlines, and blocking distractions. Be direct.",
        refinement_level="bullet-points"
    ),
    "academic": AgentConfig(
        name="Research Assistant",
        model="claude-3-opus", # Anthropic is often better for long-context research
        temperature=0.5,
        system_prompt="You are a senior academic researcher. Cite sources, use formal language, and prioritise nuance and accuracy.",
        refinement_level="detailed"
    ),
    "casual": AgentConfig(
        name="Friendly Buddy",
        model="gpt-3.5-turbo", # Cheaper model for chat
        temperature=0.9, # High temp for creativity and fun
        system_prompt="You are a supportive friend. Use emojis, be empathetic, and keep things light.",
        refinement_level="concise"
    )
}