"""
FastAPI routes for agent interactions.

This module provides HTTP endpoints for creating and interacting with agents,
making the agent functionality accessible via REST API.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.agent_project.application.services import AgentService
from src.agent_project.domain.entities import Agent
from src.agent_project.infrastructure.llm import OpenAIAdapter
from src.agent_project.infrastructure.repositories import MemoryConversationRepository


# Request/Response models
class CreateAgentRequest(BaseModel):
    name: str
    role: str = "assistant"
    system_prompt: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000


class SendMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    model: str
    is_configured: bool
    created_at: Optional[str]


class ConversationResponse(BaseModel):
    id: str
    agent_id: str
    title: Optional[str]
    message_count: int
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    agent_name: str


# Global services (in production, use dependency injection)
llm_adapter = OpenAIAdapter()
conversation_repo = MemoryConversationRepository()
agent_service = AgentService(llm_adapter, conversation_repo)

# Store agents temporarily (in production, use proper persistence)
agents_store: Dict[str, Agent] = {}

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent."""
    try:
        # Set default system prompt if not provided
        system_prompt = request.system_prompt
        if not system_prompt:
            if request.role.lower() == "researcher":
                system_prompt = "You are a research assistant. Help users find and analyze information."
            else:
                system_prompt = "You are a helpful AI assistant. Be knowledgeable, friendly, and concise."

        agent = await agent_service.create_agent(
            name=request.name,
            role=request.role,
            system_prompt=system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Store agent
        agents_store[agent.id] = agent

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role.value,
            model=agent.model,
            is_configured=agent.is_configured,
            created_at=agent.created_at.isoformat() if agent.created_at else None,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[AgentResponse])
async def list_agents():
    """List all created agents."""
    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role.value,
            model=agent.model,
            is_configured=agent.is_configured,
            created_at=agent.created_at.isoformat() if agent.created_at else None,
        )
        for agent in agents_store.values()
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a specific agent."""
    agent = agents_store.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role.value,
        model=agent.model,
        is_configured=agent.is_configured,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
    )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(agent_id: str, request: SendMessageRequest):
    """Send a message to an agent and get a response."""
    agent = agents_store.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = await conversation_repo.get_conversation(request.conversation_id)

        if not conversation:
            conversation = await agent_service.start_conversation(agent, title="API Chat")

        # Send message and get response
        response = await agent_service.send_message(conversation, agent, request.message)

        return ChatResponse(message=response, conversation_id=conversation.id, agent_name=agent.name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/conversations", response_model=List[ConversationResponse])
async def get_agent_conversations(agent_id: str):
    """Get all conversations for an agent."""
    agent = agents_store.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    conversations = await agent_service.list_agent_conversations(agent_id)

    return [
        ConversationResponse(
            id=conv.id,
            agent_id=conv.agent_id,
            title=conv.title,
            message_count=conv.message_count,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )
        for conv in conversations
    ]


@router.get("/{agent_id}/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(agent_id: str, conversation_id: str):
    """Get all messages in a conversation."""
    agent = agents_store.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    conversation = await conversation_repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.agent_id != agent_id:
        raise HTTPException(status_code=403, detail="Conversation belongs to different agent")

    return [
        MessageResponse(role=msg.role.value, content=msg.content, timestamp=msg.timestamp.isoformat())
        for msg in conversation.messages
    ]


@router.post("/quick-chat", response_model=ChatResponse)
async def quick_chat(request: SendMessageRequest):
    """Quick chat with a default assistant agent."""
    try:
        # Create or get default agent
        default_agent = None
        for agent in agents_store.values():
            if agent.name == "Default Assistant":
                default_agent = agent
                break

        if not default_agent:
            default_agent = await agent_service.create_agent(
                name="Default Assistant",
                role="assistant",
                system_prompt="You are a helpful AI assistant. Be knowledgeable, friendly, and concise.",
            )
            agents_store[default_agent.id] = default_agent

        # Create conversation
        conversation = await agent_service.start_conversation(default_agent, title="Quick Chat")

        # Send message and get response
        response = await agent_service.send_message(conversation, default_agent, request.message)

        return ChatResponse(message=response, conversation_id=conversation.id, agent_name=default_agent.name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test LLM connectivity
        health_ok = await llm_adapter.health_check()

        return {
            "status": "healthy" if health_ok else "degraded",
            "agents_count": len(agents_store),
            "llm_connection": health_ok,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
