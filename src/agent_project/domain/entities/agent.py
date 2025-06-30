"""Agent domain entity - core business logic for AI agents."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class AgentRole(str, Enum):
    """Available agent roles."""

    ASSISTANT = "assistant"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    CREATIVE = "creative"


@dataclass(frozen=True)
class Agent:
    """
    Core Agent entity representing an AI agent.

    This is the heart of our agent system - a domain entity that encapsulates
    the essential properties and behaviors of an AI agent.
    """

    id: str
    name: str
    role: AgentRole
    system_prompt: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    tools_enabled: bool = True
    memory_enabled: bool = True
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate agent configuration."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")

        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")

        if not self.name.strip():
            raise ValueError("Agent name cannot be empty")

        if not self.system_prompt.strip():
            raise ValueError("System prompt cannot be empty")

    @property
    def is_configured(self) -> bool:
        """Check if agent is properly configured."""
        return (
            bool(self.name.strip())
            and bool(self.system_prompt.strip())
            and self.model
            and 0 <= self.temperature <= 2
            and self.max_tokens > 0
        )

    def get_display_name(self) -> str:
        """Get a user-friendly display name."""
        return f"{self.name} ({self.role.value})"

    def get_model_config(self) -> Dict[str, Any]:
        """Get LLM configuration for this agent."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
        }

    @classmethod
    def create_assistant(cls, name: str, system_prompt: str, agent_id: Optional[str] = None, **kwargs) -> "Agent":
        """Factory method to create a basic assistant agent."""
        from uuid import uuid4

        return cls(
            id=agent_id or str(uuid4()),
            name=name,
            role=AgentRole.ASSISTANT,
            system_prompt=system_prompt,
            created_at=datetime.utcnow(),
            **kwargs,
        )

    @classmethod
    def create_researcher(cls, name: str, research_domain: str, agent_id: Optional[str] = None, **kwargs) -> "Agent":
        """Factory method to create a research-focused agent."""
        from uuid import uuid4

        system_prompt = f"""You are a research assistant specializing in {research_domain}.
        
Your role is to:
- Conduct thorough research on topics
- Provide well-sourced information
- Analyze data and identify patterns
- Present findings in a clear, structured manner

Always cite sources when possible and acknowledge limitations in your knowledge."""

        return cls(
            id=agent_id or str(uuid4()),
            name=name,
            role=AgentRole.RESEARCHER,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for research accuracy
            tools_enabled=True,
            created_at=datetime.utcnow(),
            **kwargs,
        )
