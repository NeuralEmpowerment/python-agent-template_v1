---
title: "ADR-006: Entity-First Database Design"
version: 2.0.0
created: 2025-06-04
updated: 2025-06-27
status: accepted
deciders: [User, AI Assistant]
tags: [adr, database, schema, entity-first, domain-driven-design, sqlalchemy, bounded-context]
related: [001, 002, 004, 005]
---

# 🗄️ ADR-006: Entity-First Database Design

> [!IMPORTANT]
> **Status:** Accepted - Domain entities are the single source of truth for database schema design. This approach ensures domain-driven design principles are maintained while supporting multiple database backends and bounded context architecture.

## Table of Contents

- [🗄️ ADR-006: Entity-First Database Design](#️-adr-006-entity-first-database-design)
  - [Table of Contents](#table-of-contents)
  - [📋 Context](#-context)
  - [🎯 Decision](#-decision)
    - [🏛️ 1. Entity-First Schema Approach](#️-1-entity-first-schema-approach)
    - [🔗 2. SQLAlchemy Imperative Mapping](#-2-sqlalchemy-imperative-mapping)
    - [🏗️ 3. Bounded Context Database Strategy](#️-3-bounded-context-database-strategy)
    - [🗃️ 4. Multi-Backend Support](#️-4-multi-backend-support)
    - [🔄 5. Schema Evolution Process](#-5-schema-evolution-process)
    - [📁 6. File Organization](#-6-file-organization)
  - [📈 Consequences](#-consequences)
    - [✅ Positive](#-positive)
    - [❌ Negative](#-negative)
    - [⚖️ Neutral](#️-neutral)
  - [🚀 Implementation](#-implementation)

[↑ Back to Top](#table-of-contents)

## 📋 Context

In a bounded context architecture where each context can potentially become a microservice, we need a database design approach that:

1. **Maintains Domain-Driven Design principles**: Domain entities are the source of truth
2. **Supports bounded context isolation**: Each context manages its own data model  
3. **Enables microservice extraction**: Data models can move with their bounded context
4. **Supports multiple backends**: SQLite for development, PostgreSQL for production
5. **Avoids schema drift**: Database schema generated from domain entities, not vice versa
6. **Provides type safety**: Python types bridge to SQL types automatically

> [!WARNING]
> Traditional database-first approaches violate domain-driven design by making infrastructure concerns drive domain design. This ADR establishes entity-first design as our standard across all bounded contexts.

[↑ Back to Top](#table-of-contents)

## 🎯 Decision

### 🏛️ 1. Entity-First Schema Approach
[↑ Back to Top](#table-of-contents)

**Domain entities are the single source of truth for database schema:**

```python
# src/agent_project/domain/entities/conversation.py
@dataclass
class Conversation:
    """Pure domain entity - source of truth for schema"""
    id: UUID
    agent_id: UUID
    title: str
    messages: List[str]
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    
    def add_message(self, message: str) -> None:
        """Domain behavior - no persistence concerns"""
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
```

**Design Principles:**
- Domain entities define structure and constraints
- Database schema is **generated from** entities, not designed separately
- Schema changes originate from domain model evolution
- Python types automatically bridge to appropriate SQL types

> [!TIP]
> This approach ensures your database design always reflects your actual business domain, preventing schema drift and maintaining consistency across bounded contexts.

### 🔗 2. SQLAlchemy Imperative Mapping
[↑ Back to Top](#table-of-contents)

**Use SQLAlchemy's imperative mapping to keep entities pure:**

```python
# Pure domain entity (no SQLAlchemy dependencies)
@dataclass
class Conversation:
    id: UUID
    agent_id: UUID
    title: str
    # ... domain fields only

# Separate SQLAlchemy mapping in infrastructure layer
# src/agent_project/infrastructure/database/mappings.py
conversation_table = Table(
    'conversations',
    mapper_registry.metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False),
    Column('title', String(255), nullable=False),
    Column('messages', JSON, nullable=False, default=list),
    Column('status', String(50), nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=False),
    Column('updated_at', DateTime(timezone=True), nullable=False),
)

# Map entity to table imperatively
mapper_registry.map_imperatively(Conversation, conversation_table)
```

**Benefits:**
- Domain entities remain completely free of persistence concerns
- SQLAlchemy mapping is separate and replaceable
- Supports multiple database backends without entity changes
- Type safety: Python types → SQL types automatically

### 🏗️ 3. Bounded Context Database Strategy
[↑ Back to Top](#table-of-contents)

**Each bounded context manages its own data model:**

```python
# Each bounded context has its own database configuration
src/
├── agent_project/                    # Bounded Context 1
│   ├── domain/entities/             # Agent-specific entities
│   │   ├── agent.py                # Agent domain model
│   │   └── conversation.py         # Conversation domain model
│   ├── infrastructure/database/
│   │   ├── mappings.py             # SQLAlchemy mappings for this context
│   │   └── repository_sqlite.py    # Context-specific repository
│   └── config/settings.py          # Context database settings
├── notification_service/            # Bounded Context 2  
│   ├── domain/entities/
│   │   ├── notification.py        # Notification domain model
│   │   └── template.py             # Template domain model
│   └── infrastructure/database/
│       └── mappings.py             # Separate mappings for notifications
└── shared/                          # Shared infrastructure
    └── database/
        ├── base.py                 # Shared database utilities
        └── factory.py              # Database connection factory
```

**Context Isolation Benefits:**
- Each context owns its data model completely
- Contexts can evolve independently
- Clean extraction path to microservices
- No cross-context database dependencies

### 🗃️ 4. Multi-Backend Support
[↑ Back to Top](#table-of-contents)

**Database-agnostic approach supporting seamless backend transitions:**

```python
# Development: SQLite per bounded context
AGENT_DATABASE_URL = "sqlite:///./data/agent_project.db"
NOTIFICATION_DATABASE_URL = "sqlite:///./data/notifications.db"

# Production: PostgreSQL with schema separation
AGENT_DATABASE_URL = "postgresql://user:pass@db:5432/app?options=-csearch_path=agent_project"
NOTIFICATION_DATABASE_URL = "postgresql://user:pass@db:5432/app?options=-csearch_path=notifications"

# Or separate databases for true microservice preparation
AGENT_DATABASE_URL = "postgresql://user:pass@agent-db:5432/agent_project"
NOTIFICATION_DATABASE_URL = "postgresql://user:pass@notification-db:5432/notifications"
```

**Backend Transition Strategy:**
- **SQLite**: Rapid local development, one file per bounded context
- **PostgreSQL Schemas**: Shared database with logical separation
- **Separate Databases**: Full microservice preparation

### 🔄 5. Schema Evolution Process
[↑ Back to Top](#table-of-contents)

**Development workflow:**
```mermaid
graph LR
    A[Modify Domain Entity] --> B[Update Mappings]
    B --> C[Run Tests]
    C --> D[SQLAlchemy Auto-Creates Schema]
    D --> E[Continue Development]
```

**Production deployment:**
```mermaid
graph LR
    A[Domain Entity Changes] --> B[Generate Migration]
    B --> C[Review Migration]
    C --> D[Apply to Production]
    D --> E[Deploy Application]
```

- **Development**: Schema auto-generated from entities
- **Production**: Migration-based deployment with review process
- **Both**: Domain entities remain the source of truth

### 📁 6. File Organization
[↑ Back to Top](#table-of-contents)

**Following ADR-004 file organization standards:**

```
src/agent_project/                           # Bounded Context
├── domain/
│   └── entities/
│       ├── agent.py                        # Agent entity
│       └── conversation.py                 # Conversation entity
├── infrastructure/
│   ├── database/
│   │   ├── mappings.py                     # SQLAlchemy entity mappings
│   │   └── session.py                     # Database session management
│   └── repositories/
│       ├── conversation_repository_interface.py
│       └── conversation_repository_sqlite.py
└── config/
    └── settings.py                         # Context database configuration
```

**Mapping Organization:**
```python
# src/agent_project/infrastructure/database/mappings.py
from sqlalchemy import Table, Column, String, DateTime, UUID, JSON
from src.agent_project.domain.entities.agent import Agent
from src.agent_project.domain.entities.conversation import Conversation

# Agent table mapping
agent_table = Table('agents', mapper_registry.metadata, ...)
mapper_registry.map_imperatively(Agent, agent_table)

# Conversation table mapping  
conversation_table = Table('conversations', mapper_registry.metadata, ...)
mapper_registry.map_imperatively(Conversation, conversation_table)
```

[↑ Back to Top](#table-of-contents)

## 📈 Consequences

### ✅ Positive
[↑ Back to Top](#table-of-contents)

- **Domain-driven design maintained**: Entities remain pure business logic
- **Bounded context isolation**: Each context owns its complete data model
- **Microservice ready**: Clean extraction path for each bounded context
- **Database-agnostic architecture**: Easy backend transitions (SQLite → PostgreSQL)
- **Schema consistency**: Database always reflects domain model
- **Type safety**: Python types automatically bridge to SQL types
- **Testability**: Can test with different repository implementations per context
- **Development velocity**: SQLite enables fast local development

### ❌ Negative
[↑ Back to Top](#table-of-contents)

- **Additional complexity**: Imperative mapping requires more setup than declarative
- **Learning curve**: Team needs to understand entity-first design principles
- **Multiple databases**: Development setup more complex with multiple SQLite files
- **Migration coordination**: Production deployments require migration planning per context

### ⚖️ Neutral
[↑ Back to Top](#table-of-contents)

- **Context boundaries**: Need clear guidelines for cross-context data relationships
- **Schema evolution**: Each context evolves independently (benefit and challenge)
- **Tooling**: May need custom tools for multi-context database operations

[↑ Back to Top](#table-of-contents)

## 🚀 Implementation

**Entity-First Database Implementation Checklist:**
- [x] Domain entities define all data structures
- [x] SQLAlchemy imperative mapping in infrastructure layer
- [x] Bounded context database isolation
- [x] Multi-backend support (SQLite → PostgreSQL)
- [x] Type-safe Python → SQL bridging

**Development Guidelines:**
1. **New Entities:** Always start with pure Python dataclass in domain layer
2. **Database Mapping:** Create imperative mapping in infrastructure layer
3. **Type Safety:** Use Python types that map clearly to SQL types
4. **Context Isolation:** Each bounded context manages its own data model
5. **Schema Evolution:** Domain changes drive database changes, never reverse

**Implementation Pattern:**
```python
# 1. Define pure domain entity
@dataclass
class MyEntity:
    id: UUID
    name: str
    created_at: datetime

# 2. Create SQLAlchemy mapping
my_table = Table('my_entities', metadata, ...)
mapper_registry.map_imperatively(MyEntity, my_table)

# 3. Implement repository
class SQLiteMyEntityRepository(MyEntityRepositoryInterface):
    def create(self, entity: MyEntity) -> str:
        # Use SQLAlchemy session with mapped entity
        pass
```

**Python Type → SQL Type Mapping:**
- `str` → `VARCHAR/TEXT`
- `int` → `INTEGER`
- `float` → `REAL/NUMERIC`
- `bool` → `BOOLEAN`
- `datetime` → `TIMESTAMP/DATETIME`
- `UUID` → `UUID` (PostgreSQL) / `TEXT` (SQLite)
- `List[T]` → `JSON`
- `Dict[str, Any]` → `JSON`

> [!NOTE]
> This approach prioritizes domain purity and bounded context isolation while supporting both monolithic development and microservice evolution through entity-first database design.

[↑ Back to Top](#table-of-contents)

---

**Database Design Version:** 2.0.0  
**Last Updated:** 2025-06-27  
**Focus:** Entity-first design, bounded context isolation, microservice readiness 