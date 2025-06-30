"""Example routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/hello")
async def hello_world() -> dict[str, str]:
    """Hello world example endpoint."""
    return {"message": "Hello, World!", "service": "examples"}


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Ping example endpoint."""
    return {"message": "pong", "service": "examples"}


@router.get("/status")
async def status() -> dict[str, str]:
    """Status example endpoint."""
    return {"status": "running", "service": "examples"}
