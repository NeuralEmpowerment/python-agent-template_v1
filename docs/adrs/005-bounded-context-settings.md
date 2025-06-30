---
title: "ADR-005: Bounded Context Settings Configuration"
version: 2.0.0
created: 2024-03-21
updated: 2025-06-27
status: accepted
deciders: [User, AI Assistant]
tags: [adr, architecture, configuration, settings, bounded-context]
related: [001, 002, 004]
---

# ⚙️ ADR-005: Bounded Context Settings Configuration

> [!IMPORTANT]
> **Status:** Accepted - This defines the settings configuration strategy for bounded context architecture with both context-specific and shared configuration.

## Table of Contents

- [⚙️ ADR-005: Bounded Context Settings Configuration](#️-adr-005-bounded-context-settings-configuration)
  - [Table of Contents](#table-of-contents)
  - [📋 Context](#-context)
  - [🎯 Decision](#-decision)
    - [🏗️ 1. Bounded Context Settings Architecture](#️-1-bounded-context-settings-architecture)
    - [🔧 2. Context-Specific Settings](#-2-context-specific-settings)
    - [🌐 3. Shared Root Settings](#-3-shared-root-settings)
    - [⚙️ 4. Configuration Composition](#️-4-configuration-composition)
    - [📦 5. Environment Management](#-5-environment-management)
  - [📈 Consequences](#-consequences)
    - [✅ Positive](#-positive)
    - [❌ Negative](#-negative)
    - [⚖️ Neutral](#️-neutral)
  - [🚀 Implementation](#-implementation)

[↑ Back to Top](#table-of-contents)

## 📋 Context

In a bounded context architecture where each context can potentially become a microservice, we need a configuration strategy that supports:

- **Context Isolation:** Each bounded context has its own configuration needs
- **Shared Configuration:** Cross-cutting concerns shared across contexts
- **Easy Extraction:** Settings can move with context when extracted to microservice
- **Development Velocity:** Simple configuration during monolithic development
- **Environment Flexibility:** Different configurations per environment

> [!NOTE]
> The previous centralized settings approach worked for a single application but doesn't scale to bounded contexts that need independent configuration.

[↑ Back to Top](#table-of-contents)

## 🎯 Decision

### 🏗️ 1. Bounded Context Settings Architecture
[↑ Back to Top](#table-of-contents)

**Two-layer configuration approach:**

```mermaid
graph TD
    A[Root Settings] --> B[Shared Configuration]
    A --> C[Database Settings]
    A --> D[Infrastructure Settings]
    
    E[Context Settings] --> F[Agent Context Config]
    E --> G[Notification Context Config]
    E --> H[Analytics Context Config]
    
    I[Application] --> A
    I --> E
```

**Configuration Structure:**
```
src/
├── config/                          # Root shared configuration
│   ├── settings.py                 # Shared settings (database, infrastructure)
│   └── environment.py              # Environment detection and loading
├── agent_project/                   # Bounded Context
│   └── config/
│       └── settings.py             # Agent-specific settings
├── notification_service/            # Another Bounded Context
│   └── config/
│       └── settings.py             # Notification-specific settings
└── analytics_engine/               # Another Bounded Context
    └── config/
        └── settings.py             # Analytics-specific settings
```

### 🔧 2. Context-Specific Settings
[↑ Back to Top](#table-of-contents)

**Each bounded context manages its own configuration:**

```python
# src/agent_project/config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional

class AgentSettings(BaseSettings):
    """Agent-specific configuration"""
    
    # Agent behavior settings
    max_conversation_length: int = Field(default=100, description="Maximum conversation turns")
    default_model: str = Field(default="gpt-4", description="Default LLM model")
    response_timeout: int = Field(default=30, description="Response timeout in seconds")
    
    # Agent-specific integrations
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Context-specific storage
    conversation_storage_path: str = Field(default="./data/conversations", description="Conversation storage")
    
    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"

# Usage within bounded context
def get_agent_settings() -> AgentSettings:
    return AgentSettings()
```

### 🌐 3. Shared Root Settings
[↑ Back to Top](#table-of-contents)

**Cross-cutting concerns at root level:**

```python
# src/config/settings.py
from pydantic import BaseSettings, Field
from typing import List

class DatabaseSettings(BaseSettings):
    """Shared database configuration"""
    url: str = Field(default="sqlite:///./app.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, description="Connection pool size")
    
    class Config:
        env_prefix = "DB_"

class InfrastructureSettings(BaseSettings):
    """Shared infrastructure configuration"""
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment")
    
    class Config:
        env_prefix = "INFRA_"

class SharedSettings(BaseSettings):
    """Root application settings"""
    app_name: str = Field(default="Agent Template", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    
    # Shared configurations
    database: DatabaseSettings = DatabaseSettings()
    infrastructure: InfrastructureSettings = InfrastructureSettings()
    
    class Config:
        env_file = ".env"

# Global shared settings instance
shared_settings = SharedSettings()
```

### ⚙️ 4. Configuration Composition
[↑ Back to Top](#table-of-contents)

**Compose settings at application startup:**

```python
# apps/main.py
from src.config.settings import shared_settings
from src.agent_project.config.settings import get_agent_settings

def create_app():
    """Create application with composed configuration"""
    
    # Load shared configuration
    db_config = shared_settings.database
    infra_config = shared_settings.infrastructure
    
    # Load context-specific configuration
    agent_config = get_agent_settings()
    
    # Initialize services with appropriate config
    database_service = DatabaseService(db_config)
    agent_service = AgentService(agent_config)
    
    return FastAPI(
        title=shared_settings.app_name,
        version=shared_settings.version
    )
```

### 📦 5. Environment Management
[↑ Back to Top](#table-of-contents)

**Environment-specific configuration:**

```bash
# .env - Development
DB_URL=sqlite:///./dev.db
INFRA_LOG_LEVEL=DEBUG
AGENT_DEFAULT_MODEL=gpt-3.5-turbo
AGENT_OPENAI_API_KEY=dev-key

# .env.production - Production
DB_URL=postgresql://user:pass@prod-db:5432/app
INFRA_LOG_LEVEL=INFO
AGENT_DEFAULT_MODEL=gpt-4
AGENT_OPENAI_API_KEY=prod-key
```

**Environment detection:**
```python
# src/config/environment.py
import os
from pathlib import Path

def get_env_file() -> str:
    """Determine which .env file to load"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    env_files = {
        "development": ".env",
        "testing": ".env.test", 
        "staging": ".env.staging",
        "production": ".env.production"
    }
    
    env_file = env_files.get(environment, ".env")
    
    if Path(env_file).exists():
        return env_file
    
    return ".env"  # Fallback
```

[↑ Back to Top](#table-of-contents)

## 📈 Consequences

### ✅ Positive
[↑ Back to Top](#table-of-contents)

- **Context Isolation:** Each bounded context manages its own configuration
- **Easy Extraction:** Context settings move with the context to microservices  
- **Shared Efficiency:** Common configuration shared across contexts
- **Environment Flexibility:** Different configurations per environment
- **Type Safety:** Pydantic provides validation and type checking
- **Clear Separation:** Business configuration separate from infrastructure
- **Development Velocity:** Simple configuration during monolithic development

### ❌ Negative
[↑ Back to Top](#table-of-contents)

- **Configuration Complexity:** More configuration files to maintain
- **Coordination Required:** Changes to shared settings affect all contexts
- **Learning Curve:** Team needs to understand two-layer approach

### ⚖️ Neutral
[↑ Back to Top](#table-of-contents)

- **Environment Variables:** Need clear naming conventions to avoid conflicts
- **Testing:** Each context needs independent test configuration
- **Documentation:** Must document which settings belong where

[↑ Back to Top](#table-of-contents)

## 🚀 Implementation

**Configuration Implementation Checklist:**
- [x] Root shared settings for infrastructure concerns
- [x] Context-specific settings for business logic
- [x] Environment-specific configuration files
- [x] Type-safe configuration with Pydantic
- [x] Clear environment variable naming conventions

**Development Guidelines:**
1. **New Bounded Context:** Create context-specific settings in `{context}/config/settings.py`
2. **Shared Concerns:** Add to root `src/config/settings.py`
3. **Environment Config:** Use prefixed environment variables
4. **Testing:** Override settings for test environments

**Migration Strategy:**
1. **Identify Configuration:** Separate business logic from infrastructure settings
2. **Create Context Settings:** Move context-specific config to bounded contexts
3. **Preserve Shared Settings:** Keep infrastructure config at root level
4. **Update Applications:** Compose configuration at startup

**Environment Variable Conventions:**
- **Shared:** `DB_*`, `INFRA_*`, `LOG_*`
- **Context Specific:** `AGENT_*`, `NOTIFICATION_*`, `ANALYTICS_*`
- **Clear Prefixes:** Avoid naming conflicts between contexts

> [!NOTE]
> This approach balances context independence with shared efficiency, supporting both monolithic development and microservice evolution.

[↑ Back to Top](#table-of-contents)

---

**Settings Version:** 2.0.0  
**Last Updated:** 2025-06-27  
**Focus:** Bounded context architecture, microservice readiness, configuration isolation 