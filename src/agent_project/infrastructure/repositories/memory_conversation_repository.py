"""In-memory conversation repository for development and testing."""

from typing import Dict, List, Optional

from src.agent_project.domain.entities import Conversation
from src.agent_project.infrastructure.logging import get_context_logger


class MemoryConversationRepository:
    """
    In-memory conversation repository.

    This repository stores conversations in memory and is perfect for
    development, testing, and simple deployments that don't need persistence.
    """

    def __init__(self) -> None:
        """Initialize the repository."""
        self._conversations: Dict[str, Conversation] = {}
        self.logger = get_context_logger()

    async def save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation."""
        self._conversations[conversation.id] = conversation
        self.logger.debug(f"Saved conversation: {conversation.id}")

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            self.logger.debug(f"Retrieved conversation: {conversation_id}")
        else:
            self.logger.debug(f"Conversation not found: {conversation_id}")
        return conversation

    async def list_conversations(self, agent_id: str) -> List[Conversation]:
        """List conversations for an agent."""
        conversations = [conv for conv in self._conversations.values() if conv.agent_id == agent_id]
        self.logger.debug(f"Found {len(conversations)} conversations for agent: {agent_id}")
        return conversations

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            self.logger.debug(f"Deleted conversation: {conversation_id}")
            return True
        return False

    async def clear_all(self) -> None:
        """Clear all conversations (useful for testing)."""
        count = len(self._conversations)
        self._conversations.clear()
        self.logger.debug(f"Cleared {count} conversations")

    def get_stats(self) -> Dict[str, int]:
        """Get repository statistics."""
        total_conversations = len(self._conversations)
        total_messages = sum(conv.message_count for conv in self._conversations.values())

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
        }
