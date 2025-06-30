#!/usr/bin/env python3
"""
Agent CLI - Command line interface for agent interactions.

This tool provides a command-line interface for creating and chatting with agents.
Perfect for testing, automation, and quick interactions.

Usage:
    python tools/agent_cli.py chat "Hello, how are you?"
    python tools/agent_cli.py interactive
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
import argparse

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from src.agent_project.domain.entities import Agent
from src.agent_project.application.services import AgentService
from src.agent_project.infrastructure.llm import OpenAIAdapter
from src.agent_project.infrastructure.repositories import MemoryConversationRepository


console = Console()


class AgentCLI:
    """Command-line interface for agent interactions."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.llm_adapter = OpenAIAdapter()
        self.conversation_repo = MemoryConversationRepository()
        self.agent_service = AgentService(self.llm_adapter, self.conversation_repo)
        self.current_agent: Optional[Agent] = None
        self.current_conversation = None
    
    async def create_default_agent(self) -> Agent:
        """Create a default assistant agent."""
        system_prompt = """You are a helpful AI assistant. You're knowledgeable, friendly, and concise.

Your role is to:
- Answer questions clearly and accurately
- Provide helpful suggestions and guidance
- Be conversational and engaging
- Admit when you don't know something

Keep your responses focused and helpful."""
        
        agent = await self.agent_service.create_agent(
            name="Assistant",
            role="assistant",
            system_prompt=system_prompt
        )
        return agent
    
    async def quick_chat(self, message: str) -> None:
        """Send a quick message to an agent."""
        try:
            # Create agent
            if not self.current_agent:
                self.current_agent = await self.create_default_agent()
                console.print(f"[green]Created agent: {self.current_agent.get_display_name()}[/green]")
            
            # Start conversation
            if not self.current_conversation:
                self.current_conversation = await self.agent_service.start_conversation(
                    self.current_agent,
                    title="CLI Chat"
                )
            
            # Send message and get response
            console.print(f"[blue]You:[/blue] {message}")
            
            with console.status("[dim]Agent is thinking...[/dim]"):
                response = await self.agent_service.send_message(
                    self.current_conversation,
                    self.current_agent,
                    message
                )
            
            console.print(Panel(
                response,
                title=f"[green]{self.current_agent.name}[/green]",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    async def interactive_mode(self) -> None:
        """Start interactive chat mode."""
        console.print(Panel(
            "[bold blue]Welcome to Agent CLI Interactive Mode![/bold blue]\\n\\n"
            "Type your messages and press Enter to chat.\\n"
            "Commands:\\n"
            "- /help - Show help\\n"
            "- /status - Show agent status\\n"
            "- /new - Start new conversation\\n"
            "- /quit - Exit",
            title="Interactive Mode",
            border_style="blue"
        ))
        
        # Create default agent
        if not self.current_agent:
            self.current_agent = await self.create_default_agent()
        
        # Start conversation
        self.current_conversation = await self.agent_service.start_conversation(
            self.current_agent,
            title="Interactive Chat"
        )
        
        console.print(f"[green]Chatting with: {self.current_agent.get_display_name()}[/green]\\n")
        
        while True:
            try:
                user_input = Prompt.ask("[blue]You[/blue]")
                
                if user_input.lower() in ["/quit", "/exit", "/q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif user_input.lower() == "/help":
                    self.show_help()
                elif user_input.lower() == "/status":
                    await self.show_agent_status()
                elif user_input.lower() == "/new":
                    self.current_conversation = await self.agent_service.start_conversation(
                        self.current_agent,
                        title="New Interactive Chat"
                    )
                    console.print("[green]Started new conversation[/green]")
                elif user_input.strip():
                    # Send message to agent
                    with console.status("[dim]Agent is thinking...[/dim]"):
                        response = await self.agent_service.send_message(
                            self.current_conversation,
                            self.current_agent,
                            user_input
                        )
                    
                    console.print(Panel(
                        response,
                        title=f"[green]{self.current_agent.name}[/green]",
                        border_style="green"
                    ))
                    console.print()  # Add spacing
                    
            except KeyboardInterrupt:
                console.print("\\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    def show_help(self) -> None:
        """Show help information."""
        help_table = Table(title="Agent CLI Commands")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="white")
        
        help_table.add_row("/help", "Show this help message")
        help_table.add_row("/status", "Show current agent status")
        help_table.add_row("/new", "Start a new conversation")
        help_table.add_row("/quit", "Exit interactive mode")
        
        console.print(help_table)
    
    async def show_agent_status(self) -> None:
        """Show current agent status."""
        if not self.current_agent:
            console.print("[yellow]No agent created yet[/yellow]")
            return
        
        status = self.agent_service.get_agent_status(self.current_agent)
        
        status_table = Table(title=f"Agent Status: {self.current_agent.name}")
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="white")
        
        for key, value in status.items():
            status_table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(status_table)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Agent CLI - Chat with AI agents")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a quick message")
    chat_parser.add_argument("message", help="Message to send to the agent")
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive chat")
    
    args = parser.parse_args()
    
    cli = AgentCLI()
    
    if args.command == "chat":
        await cli.quick_chat(args.message)
    else:
        # Default to interactive
        await cli.interactive_mode()


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        console.print("[yellow]Set your OpenAI API key: export OPENAI_API_KEY=your_key[/yellow]")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1) 