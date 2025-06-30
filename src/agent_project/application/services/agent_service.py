"""
Agent Service - Application layer orchestration.

This service coordinates between domain entities and infrastructure adapters
to provide high-level agent operations.
"""

from typing import Any, Dict, List, Optional, Protocol

from src.agent_project.domain.entities import Agent, Conversation, Message
from src.agent_project.infrastructure.logging import get_context_logger


class LLMProvider(Protocol):
    """Protocol for LLM providers (OpenAI, Anthropic, etc.)."""

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a response from the LLM."""
        ...


class ConversationRepository(Protocol):
    """Protocol for conversation persistence."""

    async def save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation."""
        ...

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        ...

    async def list_conversations(self, agent_id: str) -> List[Conversation]:
        """List conversations for an agent."""
        ...


class AgentService:
    """
    Core application service for agent operations.

    This service provides the main business operations for working with agents,
    coordinating between domain entities and infrastructure adapters.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        conversation_repo: Optional[ConversationRepository] = None,
    ) -> None:
        """Initialize the agent service."""
        self.llm_provider = llm_provider
        self.conversation_repo = conversation_repo
        self.logger = get_context_logger()

    async def create_agent(self, name: str, role: str, system_prompt: str, **kwargs) -> Agent:
        """Create a new agent."""
        self.logger.info(f"Creating new agent: {name} with role: {role}")

        # Use factory method based on role
        if role.lower() == "researcher":
            domain = kwargs.get("research_domain", "general topics")
            agent = Agent.create_researcher(name, domain, **kwargs)
        else:
            agent = Agent.create_assistant(name, system_prompt, **kwargs)

        self.logger.info(f"Agent created successfully: {agent.id}")
        return agent

    async def start_conversation(self, agent: Agent, title: Optional[str] = None) -> Conversation:
        """Start a new conversation with an agent."""
        self.logger.info(f"Starting conversation with agent: {agent.get_display_name()}")

        conversation = Conversation.create(agent_id=agent.id, title=title or f"Chat with {agent.name}")

        # Add system prompt as first message if agent has one
        if agent.system_prompt:
            conversation.add_message(Message.system_message(agent.system_prompt))

        if self.conversation_repo:
            await self.conversation_repo.save_conversation(conversation)

        self.logger.info(f"Conversation started: {conversation.id}")
        return conversation

    async def send_message(self, conversation: Conversation, agent: Agent, user_message: str) -> str:
        """Send a message to an agent and get a response."""
        self.logger.info(
            f"Processing message in conversation {conversation.id} " f"for agent {agent.get_display_name()}"
        )

        # Add user message to conversation
        conversation.add_user_message(user_message)

        try:
            # Get LLM response
            messages = conversation.get_messages_for_llm()
            config = agent.get_model_config()

            response = await self.llm_provider.generate_response(
                messages=messages,
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            # Add assistant response to conversation
            conversation.add_assistant_message(response)

            # Save conversation if repository is available
            if self.conversation_repo:
                await self.conversation_repo.save_conversation(conversation)

            self.logger.info(f"Message processed successfully for conversation {conversation.id}")
            return response

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            conversation.add_assistant_message(error_response)

            if self.conversation_repo:
                await self.conversation_repo.save_conversation(conversation)

            return error_response

    async def get_conversation_history(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation history."""
        if not self.conversation_repo:
            self.logger.warning("No conversation repository configured")
            return None

        return await self.conversation_repo.get_conversation(conversation_id)

    async def list_agent_conversations(self, agent_id: str) -> List[Conversation]:
        """List all conversations for an agent."""
        if not self.conversation_repo:
            self.logger.warning("No conversation repository configured")
            return []

        return await self.conversation_repo.list_conversations(agent_id)

    def get_agent_status(self, agent: Agent) -> Dict[str, Any]:
        """Get status information about an agent."""
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "model": agent.model,
            "is_configured": agent.is_configured,
            "tools_enabled": agent.tools_enabled,
            "memory_enabled": agent.memory_enabled,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
        }
