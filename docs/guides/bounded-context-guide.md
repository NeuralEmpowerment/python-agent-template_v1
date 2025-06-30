# Bounded Context Guide

This guide explains how to copy and reuse the `agent_project` bounded context to create new services in your monolithic monorepo.

## 🎯 What is a Bounded Context?

A **bounded context** is a central pattern in Domain-Driven Design (DDD) that defines a boundary within which a domain model is consistent and unambiguous. In our agent template:

- `src/agent_project/` is a complete bounded context
- It contains all layers: domain, application, infrastructure, config
- It's self-contained and can be extracted as a microservice
- It follows Clean Architecture principles

## 📦 Bounded Context Structure

```
src/agent_project/                 # 🔄 COPYABLE BOUNDED CONTEXT
├── domain/                       # Core business logic
│   ├── entities/                # Business entities (Agent, Conversation)
│   └── events/                  # Domain events
├── application/                  # Use cases and services
│   └── services/               # Application services
├── infrastructure/              # External integrations  
│   ├── llm/                    # LLM adapters (OpenAI, Anthropic)
│   ├── repositories/           # Data persistence
│   └── event_bus/              # Event handling
└── config/                      # Bounded context configuration
```

## 🚀 How to Copy a Bounded Context

### Step 1: Copy the Directory

```bash
# Copy the entire bounded context
cp -r src/agent_project src/recommendation_engine

# Or for a new agent variant
cp -r src/agent_project src/research_agent
```

### Step 2: Update Imports

Update all internal imports to use the new bounded context name:

```bash
# Replace all internal imports
find src/recommendation_engine -name "*.py" -exec sed -i '' 's/src\.agent_project/src.recommendation_engine/g' {} \;
```

### Step 3: Update Configuration

Modify the config files to reflect the new service:

```python
# src/recommendation_engine/config/settings.py
class RecommendationSettings(BaseSettings):
    service_name: str = "recommendation-engine"
    # ... rest of your configuration
```

### Step 4: Customize Domain Logic

Replace the agent-specific domain logic with your new domain:

```python
# src/recommendation_engine/domain/entities/recommendation.py
@dataclass(frozen=True)
class Recommendation:
    id: str
    user_id: str
    item_id: str
    score: float
    reason: str
    # ... your domain-specific fields
```

### Step 5: Update Application Services

Adapt the application services for your new domain:

```python
# src/recommendation_engine/application/services/recommendation_service.py
class RecommendationService:
    def __init__(self, model_adapter: ModelProvider):
        self.model_adapter = model_adapter
    
    async def generate_recommendations(self, user_id: str) -> List[Recommendation]:
        # Your business logic here
        pass
```

## 🛠️ Quick Copy Script

Create this script to automate the copying process:

```bash
#!/bin/bash
# scripts/copy_bounded_context.sh

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_context> <new_context>"
    echo "Example: $0 agent_project recommendation_engine"
    exit 1
fi

SOURCE=$1
TARGET=$2

echo "🔄 Copying bounded context from $SOURCE to $TARGET..."

# Copy directory
cp -r "src/$SOURCE" "src/$TARGET"

# Update imports
echo "📝 Updating imports..."
find "src/$TARGET" -name "*.py" -exec sed -i '' "s/src\\.$SOURCE/src.$TARGET/g" {} \\;

# Update test imports
echo "📝 Updating test imports..."
find tests -name "*.py" -exec sed -i '' "s/src\\.$SOURCE/src.$TARGET/g" {} \\;

echo "✅ Bounded context copied successfully!"
echo "🔧 Next steps:"
echo "   1. Update domain entities in src/$TARGET/domain/"
echo "   2. Modify application services in src/$TARGET/application/"
echo "   3. Adapt infrastructure for your needs"
echo "   4. Update configuration in src/$TARGET/config/"
```

## 🎨 Customization Examples

### Example 1: E-commerce Recommendation Engine

```python
# src/recommendation_engine/domain/entities/
class Product:
    id: str
    name: str
    category: str
    price: float

class UserPreferences:
    user_id: str
    categories: List[str]
    price_range: Tuple[float, float]

class Recommendation:
    user_id: str
    product: Product
    score: float
    reasoning: str
```

### Example 2: Document Processing Service

```python
# src/document_processor/domain/entities/
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    status: ProcessingStatus

class ProcessingJob:
    id: str
    document_id: str
    pipeline_steps: List[ProcessingStep]
    current_step: int
```

### Example 3: User Management Service

```python
# src/user_management/domain/entities/
class User:
    id: str
    email: str
    profile: UserProfile
    permissions: Set[Permission]

class Session:
    id: str
    user_id: str
    expires_at: datetime
    metadata: Dict[str, Any]
```

## 🧪 Testing Your New Bounded Context

1. **Copy Tests**: Copy and adapt the test structure
```bash
cp -r tests/unit/agent_project tests/unit/recommendation_engine
```

2. **Update Test Imports**: Update all test imports to use your new context

3. **Run Tests**: Ensure everything works
```bash
poetry run pytest tests/unit/recommendation_engine/ -v
```

## 🚀 Deployment Considerations

### Monolithic Deployment
- All bounded contexts run in the same process
- Shared infrastructure and configuration
- Fast inter-service communication

### Microservice Extraction
When ready to extract as a microservice:

1. **Create Separate Repository**
```bash
# Copy just the bounded context
cp -r src/recommendation_engine ../recommendation-service/src/
```

2. **Add Service Infrastructure**
- Separate `pyproject.toml`
- Independent deployment pipeline
- Service discovery configuration

3. **Update Communication**
- Replace in-memory calls with HTTP/gRPC
- Add API versioning
- Implement circuit breakers

## 📋 Best Practices

### ✅ Do's
- Keep each bounded context focused on a single domain
- Maintain clear boundaries between contexts
- Use dependency injection for infrastructure
- Write comprehensive tests for each context
- Document your domain model clearly

### ❌ Don'ts  
- Don't share domain entities between contexts
- Don't create circular dependencies
- Don't expose internal implementation details
- Don't skip the domain modeling phase
- Don't ignore data consistency boundaries

## 🔄 Evolution Strategies

### 1. Start Monolithic
```
All bounded contexts in one repository/deployment
├── src/agent_project/
├── src/recommendation_engine/
├── src/user_management/
└── src/notification_service/
```

### 2. Extract When Needed
```
Separate repositories for independent teams
agent-service/
├── src/agent_project/

recommendation-service/  
├── src/recommendation_engine/

user-service/
├── src/user_management/
```

## 📚 Additional Resources

- [Domain-Driven Design Reference](https://www.domainlanguage.com/ddd/)
- [Clean Architecture Guide](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Microservices vs Monolith](https://martinfowler.com/articles/microservice-trade-offs.html)

---

Happy building! 🚀 Remember: start with a monolith, extract microservices when you have clear team and business boundaries. 