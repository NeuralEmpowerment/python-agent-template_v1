#!/bin/bash
# scripts/copy_bounded_context.sh
#
# This script helps you copy and adapt bounded contexts for new services.
# It automatically handles import updates and provides guidance for customization.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check arguments
if [ "$#" -ne 2 ]; then
    print_error "Usage: $0 <source_context> <new_context>"
    echo "Example: $0 agent_project recommendation_engine"
    echo "Example: $0 agent_project user_management"
    exit 1
fi

SOURCE=$1
TARGET=$2

# Validate source exists
if [ ! -d "src/$SOURCE" ]; then
    print_error "Source bounded context 'src/$SOURCE' does not exist"
    exit 1
fi

# Check if target already exists
if [ -d "src/$TARGET" ]; then
    print_warning "Target 'src/$TARGET' already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled"
        exit 1
    fi
    rm -rf "src/$TARGET"
fi

print_status "Copying bounded context from '$SOURCE' to '$TARGET'..."

# Copy directory
cp -r "src/$SOURCE" "src/$TARGET"
print_success "Directory copied"

# Update imports in the new bounded context
print_status "Updating imports in bounded context..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    find "src/$TARGET" -name "*.py" -exec sed -i '' "s/src\\.$SOURCE/src.$TARGET/g" {} \;
else
    # Linux
    find "src/$TARGET" -name "*.py" -exec sed -i "s/src\\.$SOURCE/src.$TARGET/g" {} \;
fi
print_success "Imports updated in bounded context"

# Update test imports if tests exist
if [ -d "tests" ]; then
    print_status "Updating test imports..."
    
    # Copy test structure if it exists
    if [ -d "tests/unit/$SOURCE" ]; then
        cp -r "tests/unit/$SOURCE" "tests/unit/$TARGET"
        print_success "Test structure copied"
        
        # Update test imports
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            find "tests/unit/$TARGET" -name "*.py" -exec sed -i '' "s/src\\.$SOURCE/src.$TARGET/g" {} \;
        else
            # Linux
            find "tests/unit/$TARGET" -name "*.py" -exec sed -i "s/src\\.$SOURCE/src.$TARGET/g" {} \;
        fi
        print_success "Test imports updated"
    else
        print_warning "No tests found for source context"
    fi
fi

# Create a basic customization checklist
cat > "src/$TARGET/CUSTOMIZATION_TODO.md" << EOF
# Customization Checklist for $TARGET

This file was auto-generated when copying from $SOURCE.
Delete this file when customization is complete.

## 🔧 Required Changes

### 1. Domain Layer (src/$TARGET/domain/)
- [ ] Update entity models to reflect your domain
- [ ] Modify or remove Agent and Conversation entities  
- [ ] Add your domain-specific entities
- [ ] Update domain events if needed

### 2. Application Layer (src/$TARGET/application/)
- [ ] Rename AgentService to ${TARGET^}Service
- [ ] Update service methods for your use cases
- [ ] Modify protocols/interfaces as needed

### 3. Infrastructure Layer (src/$TARGET/infrastructure/)
- [ ] Update LLM adapters if not needed
- [ ] Modify repositories for your entities
- [ ] Adapt event bus if using events
- [ ] Update external service integrations

### 4. Configuration (src/$TARGET/config/)
- [ ] Update service name in settings
- [ ] Modify configuration classes
- [ ] Update environment variables
- [ ] Adapt validation logic

### 5. Tests (tests/unit/$TARGET/)
- [ ] Update test cases for new entities
- [ ] Modify service tests
- [ ] Adapt integration tests
- [ ] Update mock configurations

## 🚀 Next Steps

1. Start with the domain layer - define your core entities
2. Update the application services
3. Adapt infrastructure as needed
4. Run tests: \`poetry run pytest tests/unit/$TARGET/ -v\`
5. Update API routes if needed
6. Add to main application routing

## 📚 Resources

- See docs/BOUNDED_CONTEXT_GUIDE.md for detailed guidance
- Domain-Driven Design patterns and examples
- Clean Architecture principles

---
Happy coding! 🎉
EOF

print_success "Created customization checklist: src/$TARGET/CUSTOMIZATION_TODO.md"

echo
print_success "Bounded context copied successfully!"
echo
print_status "📋 Summary:"
echo "   ✅ Copied src/$SOURCE → src/$TARGET"
echo "   ✅ Updated all imports"
if [ -d "tests/unit/$TARGET" ]; then
    echo "   ✅ Copied and updated tests"
fi
echo "   ✅ Created customization checklist"
echo
print_status "🔧 Next steps:"
echo "   1. Review src/$TARGET/CUSTOMIZATION_TODO.md"
echo "   2. Start with domain entities in src/$TARGET/domain/"
echo "   3. Update application services in src/$TARGET/application/"
echo "   4. Test your changes: poetry run pytest tests/unit/$TARGET/ -v"
echo "   5. Add API routes if needed"
echo
print_warning "Don't forget to delete CUSTOMIZATION_TODO.md when done!"
echo 