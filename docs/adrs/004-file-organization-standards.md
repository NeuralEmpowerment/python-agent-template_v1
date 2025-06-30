---
title: "ADR-004: File Organization Standards"
version: 2.0.0
created: 2025-04-15
updated: 2025-06-27
status: accepted
deciders: [User, AI Assistant]
tags: [adr, architecture, convention, naming, bounded-context]
related: [001, 002]
---

# 📄 ADR-004: File Organization Standards

> [!IMPORTANT]
> **Status:** Accepted - This defines the file naming and organization conventions for bounded context architecture.

## Table of Contents

- [📄 ADR-004: File Organization Standards](#-adr-004-file-organization-standards)
  - [Table of Contents](#table-of-contents)
  - [📋 Context](#-context)
  - [🎯 Decision](#-decision)
    - [🏗️ 1. Bounded Context Structure](#️-1-bounded-context-structure)
    - [🎯 2. General File Naming](#-2-general-file-naming)
    - [📊 3. Repository Pattern Naming](#-3-repository-pattern-naming)
    - [⚙️ 4. Service Pattern Naming](#️-4-service-pattern-naming)
    - [🏗️ 5. Domain Entity Naming](#️-5-domain-entity-naming)
    - [📁 6. Bounded Context Organization](#-6-bounded-context-organization)
  - [📈 Consequences](#-consequences)
    - [✅ Positive](#-positive)
    - [❌ Negative](#-negative)
  - [🚀 Implementation](#-implementation)

[↑ Back to Top](#table-of-contents)

## 📋 Context

We need a consistent way to name files and structure classes/interfaces within bounded contexts and DDD layers (domain, application, infrastructure) to ensure clarity and ease of navigation while maintaining domain co-location for development velocity and future microservice extraction.

> [!NOTE]
> Each bounded context in `src/` can potentially become a microservice, so file organization must support both monolithic development and future extraction.

[↑ Back to Top](#table-of-contents)

## 🎯 Decision

### 🏗️ 1. Bounded Context Structure
[↑ Back to Top](#table-of-contents)

**Each bounded context follows this structure:**

```
src/{bounded_context_name}/
├── domain/                     # Pure business logic
│   ├── entities/              # Domain entities
│   └── events/                # Domain events
├── application/               # Use cases and workflows
│   └── services/              # Application services
├── infrastructure/            # External integrations
│   ├── repositories/          # Data persistence
│   ├── llm/                   # LLM adapters
│   └── event_bus/             # Event handling
└── config/                    # Bounded context configuration
    └── settings.py            # Context-specific settings
```

### 🎯 2. General File Naming
[↑ Back to Top](#table-of-contents)

- **One Concept Per File:** Each distinct class, interface, or implementation in its own Python file
- **Snake Case:** Use `snake_case` for all file names
- **Descriptive Names:** Files named after the primary concept they represent
- **Context Prefix:** Domain-specific files prefixed with domain name for clarity

### 📊 3. Repository Pattern Naming
[↑ Back to Top](#table-of-contents)

**Standardized naming convention:**

- **File Pattern:** `{domain}_repository_{implementation}.py`
- **Class Pattern:** `{Implementation}{Domain}Repository`
- **Interface Pattern:** `{domain}_repository_interface.py` → `{Domain}RepositoryInterface`

**Examples within a bounded context:**
```
src/agent_project/infrastructure/repositories/
├── conversation_repository_interface.py    → ConversationRepositoryInterface
├── conversation_repository_memory.py       → MemoryConversationRepository
├── conversation_repository_sqlite.py       → SQLiteConversationRepository
├── agent_repository_interface.py           → AgentRepositoryInterface
└── agent_repository_memory.py              → MemoryAgentRepository
```

### ⚙️ 4. Service Pattern Naming
[↑ Back to Top](#table-of-contents)

- **Interface files:** `{domain}_service_interface.py` → `{Domain}ServiceInterface`
- **Implementation files:** `{domain}_service_{implementation}.py` → `{Implementation}{Domain}Service`

**Examples:**
```
src/agent_project/application/services/
├── agent_service.py                        → AgentService
└── conversation_service.py                 → ConversationService

src/agent_project/infrastructure/llm/
├── llm_service_interface.py               → LLMServiceInterface
├── llm_service_openai.py                  → OpenAILLMService
└── llm_service_mock.py                    → MockLLMService
```

### 🏗️ 5. Domain Entity Naming
[↑ Back to Top](#table-of-contents)

- **Entity files:** `{domain}.py` → `{Domain}`
- **Simple, clear domain names without "entity" suffix**

**Examples:**
```
src/agent_project/domain/entities/
├── agent.py                               → Agent
├── conversation.py                        → Conversation
└── message.py                             → Message
```

### 📁 6. Bounded Context Organization
[↑ Back to Top](#table-of-contents)

**Domain co-location with alphabetical ordering:**

```
src/agent_project/                          # Bounded Context
├── domain/
│   ├── entities/
│   │   ├── agent.py                       # Agent entity
│   │   └── conversation.py                # Conversation entity
│   └── events/
│       └── base.py                        # Base domain events
├── application/
│   └── services/
│       └── agent_service.py               # Agent application service
├── infrastructure/
│   ├── repositories/
│   │   ├── conversation_repository_interface.py
│   │   └── memory_conversation_repository.py
│   └── llm/
│       └── openai_adapter.py              # LLM integration
└── config/
    └── settings.py                        # Context-specific settings
```

> [!TIP]
> This organization ensures alphabetical sorting places interfaces before implementations, maintains domain co-location, and supports microservice extraction.

[↑ Back to Top](#table-of-contents)

## 📈 Consequences

### ✅ Positive
[↑ Back to Top](#table-of-contents)

- **Predictable naming:** Clear patterns for file and class names
- **Bounded context clarity:** Each context is self-contained and extractable
- **Domain co-location:** Related files grouped together for easy navigation
- **Alphabetical ordering:** Interface files appear before implementations
- **Implementation clarity:** File names immediately indicate the implementation type
- **Scalable pattern:** Easy to add new implementations and bounded contexts
- **Microservice ready:** Clean extraction path for future microservices

### ❌ Negative
[↑ Back to Top](#table-of-contents)

- **Longer filenames:** More descriptive names result in longer file names
- **Learning curve:** Team needs to understand and follow the established patterns
- **Consistency requirement:** Requires discipline to maintain naming consistency across contexts

[↑ Back to Top](#table-of-contents)

## 🚀 Implementation

**File Organization Checklist:**
- [x] Each bounded context follows standard structure
- [x] Repository interfaces defined before implementations
- [x] Domain entities use simple, clear names
- [x] Application services coordinate domain operations
- [x] Infrastructure implementations provide concrete behavior

**Development Guidelines:**
1. **New Bounded Context:** Create using standard directory structure
2. **New Domain Concepts:** Follow entity and repository naming patterns
3. **New Implementations:** Use consistent implementation suffixes
4. **File Placement:** Respect layer boundaries and co-location principles

**Migration Strategy:**
1. **Existing Files:** Gradually migrate to follow naming conventions
2. **New Development:** Strictly follow established patterns
3. **Refactoring:** Update imports when files are renamed

> [!NOTE]
> This approach prioritizes explicitness, discoverability, development velocity, consistency, and scalability while supporting both monolithic development and microservice evolution.

[↑ Back to Top](#table-of-contents)

---

**File Organization Version:** 2.0.0  
**Last Updated:** 2025-06-27  
**Focus:** Bounded context architecture, microservice readiness, development velocity 