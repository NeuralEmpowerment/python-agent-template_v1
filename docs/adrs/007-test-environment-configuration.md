# ADR-007: Test Environment Configuration and Fixture Management

**Status:** Accepted  
**Date:** 2025-01-17  
**Deciders:** Development Team  
**Technical Story:** Fix GitHub Actions test failures through comprehensive test environment configuration

## Context

The GitHub Actions CI pipeline is failing with 6 test failures and 2 errors, primarily due to:

1. **Missing Test Fixtures**: Tests reference `test_data_dir` fixture that doesn't exist
2. **Database Configuration Inconsistency**: Tests not using the configured in-memory database
3. **Test Isolation Issues**: File system operations lack proper temporary directory management
4. **CI Environment Permissions**: SQLite file access issues in GitHub Actions environment

### Current State
- `conftest.py` sets `DATABASE_URL=sqlite:///:memory:` but database tests still fail
- Environment setup tests fail due to missing `test_data_dir` fixture
- Tests pollute global state and don't clean up properly
- No standardized approach to test isolation

### Business Impact
- Template users cannot rely on CI pipeline
- Contributors cannot validate changes before merge
- Reduces confidence in template quality and reliability

## Decision

We will implement a comprehensive test environment configuration system with proper fixture management to ensure:

1. **Complete Test Isolation**: Each test runs in isolated environment
2. **Consistent Database Configuration**: All tests use in-memory database consistently  
3. **Proper Resource Management**: Automatic cleanup of temporary resources
4. **CI/Local Parity**: Tests behave identically in local and CI environments

### Key Components:

#### Test Fixtures Architecture
```python
@pytest.fixture
def test_data_dir(tmp_path):
    """Isolated temporary directory for file operations"""

@pytest.fixture  
def test_database_config():
    """Test-specific database configuration with in-memory SQLite"""

@pytest.fixture(autouse=True)
def test_environment_isolation():
    """Automatic environment cleanup and restoration"""
```

#### Database Test Strategy
- Force all tests to use `sqlite:///:memory:`
- Reset global SQLAlchemy engine/session state between tests
- Provide clean database fixtures for each test class
- Ensure no file-based database access in tests

#### File System Operations
- All file operations use pytest's `tmp_path` fixtures
- Working directory restoration after each test
- Proper cleanup of temporary files and directories

## Alternatives Considered

### Alternative 1: Minimal Fixture Addition
**Approach**: Only add missing `test_data_dir` fixture
- ❌ **Rejected**: Doesn't address database configuration issues
- ❌ **Rejected**: No comprehensive solution for test isolation

### Alternative 2: Mock All External Dependencies  
**Approach**: Mock database and file system operations
- ❌ **Rejected**: Reduces test coverage of actual infrastructure
- ❌ **Rejected**: Complex mock management overhead
- ❌ **Rejected**: Doesn't test real integration paths

### Alternative 3: Separate Test Database Files
**Approach**: Use unique SQLite files per test
- ❌ **Rejected**: CI permission issues persist
- ❌ **Rejected**: Cleanup complexity
- ❌ **Rejected**: Slower than in-memory database

## Consequences

### Positive
- ✅ **Reliable CI Pipeline**: All tests pass consistently in GitHub Actions
- ✅ **Improved Test Isolation**: Tests don't interfere with each other
- ✅ **Better Developer Experience**: Clear, predictable test behavior
- ✅ **Future-Proof**: Template for adding new tests with proper isolation
- ✅ **Documentation**: Clear patterns for test writing

### Negative  
- ⚠️ **Initial Setup Time**: Requires refactoring existing tests
- ⚠️ **Learning Curve**: Developers need to understand new fixture patterns
- ⚠️ **Maintenance**: Additional test infrastructure to maintain

### Risks and Mitigation
- **Risk**: Breaking existing tests during refactor
  - **Mitigation**: Implement incrementally, validate each milestone
- **Risk**: Performance impact of comprehensive isolation
  - **Mitigation**: Use appropriate fixture scoping, in-memory database
- **Risk**: Complexity in test debugging
  - **Mitigation**: Clear fixture documentation, error logging

## Implementation Details

### Phase 1: Core Fixture Implementation
```python
# conftest.py additions
@pytest.fixture
def test_data_dir(tmp_path):
    """Provide isolated temporary directory for each test."""
    return tmp_path

@pytest.fixture
def test_database_config():
    """Provide test-specific database configuration."""
    return DatabaseConfig(database_url="sqlite:///:memory:")

@pytest.fixture(autouse=True)
def test_environment_isolation():
    """Ensure clean environment for each test."""
    # Environment variable isolation
    # Working directory restoration  
    # Global state cleanup
```

### Phase 2: Database Test Integration
- Modify SQLAlchemy configuration tests to use fixtures
- Add database state reset between tests
- Ensure proper session/engine cleanup

### Phase 3: File System Test Safety
- Update environment setup tests to use `test_data_dir`
- Add working directory restoration
- Implement safe file operation patterns

### Compliance Requirements
- All new tests must use proper fixtures
- Database tests must use in-memory configuration
- File operations must use temporary directories
- Environment variables must be properly isolated

## Monitoring and Success Metrics

### Success Criteria
- ✅ GitHub Actions pipeline passes all tests
- ✅ No test failures or errors
- ✅ Tests pass consistently in local and CI environments
- ✅ Test execution time remains reasonable (<2 minutes)

### Monitoring
- CI pipeline success rate
- Test execution time tracking
- Test failure pattern analysis
- Developer feedback on test reliability

## References

- [GitHub Actions Test Failures Issue](PROJECT-PLAN_20250117_Fix-GitHub-Actions-Tests.md)
- [Pytest Fixture Documentation](https://docs.pytest.org/en/stable/fixture.html)
- [SQLAlchemy Testing Patterns](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Agent Template Testing Strategy](../development/environment.md)

---
**Related ADRs:**
- [ADR-004: File Organization Standards](004-file-organization-standards.md)
- [ADR-006: Entity-First Database Design](006-entity-first-database-design.md) 