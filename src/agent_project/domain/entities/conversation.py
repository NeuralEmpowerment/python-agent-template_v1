"""Conversation domain entities for managing agent interactions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class MessageRole(str, Enum):
    """Message roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class Message:
    """A single message in a conversation."""

    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate message."""
        if not self.content.strip():
            raise ValueError("Message content cannot be empty")

    @classmethod
    def user_message(cls, content: str, message_id: Optional[str] = None) -> "Message":
        """Create a user message."""
        return cls(
            id=message_id or str(uuid4()),
            role=MessageRole.USER,
            content=content.strip(),
            timestamp=datetime.utcnow(),
        )

    @classmethod
    def assistant_message(cls, content: str, message_id: Optional[str] = None) -> "Message":
        """Create an assistant message."""
        return cls(
            id=message_id or str(uuid4()),
            role=MessageRole.ASSISTANT,
            content=content.strip(),
            timestamp=datetime.utcnow(),
        )

    @classmethod
    def system_message(cls, content: str, message_id: Optional[str] = None) -> "Message":
        """Create a system message."""
        return cls(
            id=message_id or str(uuid4()),
            role=MessageRole.SYSTEM,
            content=content.strip(),
            timestamp=datetime.utcnow(),
        )


@dataclass
class Conversation:
    """A conversation between a user and an agent."""

    id: str
    agent_id: str
    title: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = None

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def add_user_message(self, content: str) -> Message:
        """Add a user message and return it."""
        message = Message.user_message(content)
        self.add_message(message)
        return message

    def add_assistant_message(self, content: str) -> Message:
        """Add an assistant message and return it."""
        message = Message.assistant_message(content)
        self.add_message(message)
        return message

    def get_last_message(self) -> Optional[Message]:
        """Get the most recent message."""
        return self.messages[-1] if self.messages else None

    def get_user_messages(self) -> List[Message]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]

    def get_assistant_messages(self) -> List[Message]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API calls."""
        return [{"role": msg.role.value, "content": msg.content} for msg in self.messages]

    def get_conversation_summary(self) -> str:
        """Get a brief summary of the conversation."""
        if not self.messages:
            return "Empty conversation"

        user_count = len(self.get_user_messages())
        assistant_count = len(self.get_assistant_messages())

        title = self.title or "Untitled Conversation"
        return f"{title} - {user_count} user messages, {assistant_count} responses"

    @property
    def message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    @property
    def is_empty(self) -> bool:
        """Check if conversation has no messages."""
        return len(self.messages) == 0

    @classmethod
    def create(
        cls,
        agent_id: str,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> "Conversation":
        """Create a new conversation."""
        return cls(id=conversation_id or str(uuid4()), agent_id=agent_id, title=title)
