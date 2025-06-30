---
title: Development Gotchas and Solutions
version: 1.0.0
created: 2025-04-15
updated: 2025-06-06
tags: [development, gotchas, troubleshooting, tips]
---

# 🚧 Development Gotchas and Solutions

This document contains solutions to common issues you might encounter while working with this codebase.

## 📑 Table of Contents

- [🚧 Development Gotchas and Solutions](#-development-gotchas-and-solutions)
  - [📑 Table of Contents](#-table-of-contents)
  - [🔥 Critical Database Persistence Issues](#-critical-database-persistence-issues)
    - [Silent Transcription Database Save Failures](#silent-transcription-database-save-failures)
  - [Poe the Poet Task Runner Issues](#-poe-the-poet-task-runner-issues)
    - [ignore\_fail Option Not Supported](#ignore_fail-option-not-supported)
  - [Pydantic v2 Configuration](#-pydantic-v2-configuration)
    - [Class-based Config Deprecation](#class-based-config-deprecation)
    - [Field Exclusion Pattern](#field-exclusion-pattern)
  - [Python Import Issues](#-python-import-issues)
    - [Module Import Path Conflict](#module-import-path-conflict)
    - [PYTHONPATH in Tests](#pythonpath-in-tests)
  - [Supabase Client Type Issues](#-supabase-client-type-issues)
    - [Response Object Access](#response-object-access)
  - [Mypy Type Checking](#-mypy-type-checking)
    - [Test Function Return Types](#test-function-return-types)
  - [Datetime Handling](#-datetime-handling)
    - [datetime.utcnow() Deprecation](#datetimeutcnow-deprecation)
  - [Line Length Conflicts](#-line-length-conflicts)
    - [Black and Ruff Disagreement](#black-and-ruff-disagreement)
  - [Supabase Storage Issues](#-supabase-storage-issues)
    - [Downloading Files from Supabase Storage](#downloading-files-from-supabase-storage)
  - [Environment Variable Inheritance Issues](#-environment-variable-inheritance-issues)
    - [Poetry/Poe Tasks Not Loading Environment Variables](#poetrypoe-tasks-not-loading-environment-variables)

## 🔥 Critical Database Persistence Issues

### Silent Transcription Database Save Failures

**CRITICAL ISSUE**: Transcriptions appear to complete successfully through the API and ZenML pipelines, but are not actually saved to the database, causing retrieval to fail with "not_found" errors.

**Symptoms:**
- API reports `"status": "completed"` for transcription requests
- ZenML logs show successful transcription step completion with transcription IDs
- Database queries return no records for the transcription
- E2E tests fail because transcription results cannot be retrieved
- No error messages or exceptions in application logs

**Example:**
```bash
# API reports success
curl -X POST "/audio/upload-and-transcribe" -F "file=@audio.m4a"
# Returns: {"status": "completed", "transcription_id": "abc123"}

# But retrieval fails
curl -X GET "/audio/{audio_id}/transcription"  
# Returns: {"status": "not_found", "message": "No transcription found"}

# Database shows no recent records despite API success
sqlite3 ./data/transcriptions.db "SELECT COUNT(*) FROM transcriptions WHERE created_at > '2025-06-06 15:30:00';"
# Returns: 0
```

**Root Cause:**
The issue occurs in the database persistence layer where transcription entities are created and appear to be saved, but the database transaction fails silently. The problem manifests in:

1. **SQLite Transaction Management**: The session context manager commits transactions, but certain conditions cause silent rollbacks
2. **Entity Mapping Issues**: Potential mismatch between entity fields and database schema
3. **Silent Exception Handling**: Database errors may be caught and not properly logged
4. **Session Lifecycle Problems**: Database sessions may not be properly committed in certain execution contexts

**Investigation Steps:**

1. **Check database session commits**:
   ```python
   # Add debug logging to SQLiteTranscriptionRepository.create()
   with get_database_session() as session:
       try:
           session.execute(text("INSERT INTO..."), params)
           print(f"DEBUG: About to commit transcription {transcription.id}")
           # session.commit() happens in context manager
           print(f"DEBUG: Transcription {transcription.id} committed successfully")
       except Exception as e:
           print(f"DEBUG: Database error during transcription save: {e}")
           raise
   ```

2. **Verify transaction isolation**:
   ```bash
   # Check if transcription was inserted in a separate transaction
   sqlite3 ./data/transcriptions.db "SELECT id, created_at FROM transcriptions ORDER BY created_at DESC LIMIT 5;"
   ```

3. **Add comprehensive error logging**:
   ```python
   # In transcription_service_local.py transcribe() method
   try:
       self.transcription_repository.create(transcription)
       logger.info(f"DEBUG: Transcription {transcription.id} saved to repository")
       
       # Immediately verify the save
       saved_transcription = self.transcription_repository.read(transcription.id)
       if saved_transcription:
           logger.info(f"DEBUG: Transcription {transcription.id} verified in database")
       else:
           logger.error(f"ERROR: Transcription {transcription.id} NOT found after save!")
   except Exception as e:
       logger.error(f"ERROR: Failed to save transcription: {e}")
       raise
   ```

**Immediate Fix:**
Add explicit transaction verification to the repository create method:

```python
# In SQLiteTranscriptionRepository.create()
def create(self, transcription: Transcription) -> str:
    if not transcription.id:
        transcription.id = str(uuid4())

    with get_database_session() as session:
        try:
            session.execute(text("INSERT INTO..."), self._transcription_to_db_params(transcription))
            session.flush()  # Force write to database
            
            # Verify the record was actually saved
            verification = session.execute(
                text("SELECT id FROM transcriptions WHERE id = :id"),
                {"id": transcription.id}
            ).fetchone()
            
            if not verification:
                raise RuntimeError(f"Transcription {transcription.id} was not saved to database")
                
            return transcription.id
        except SQLAlchemyError as e:
            logger.error(f"Database error saving transcription {transcription.id}: {e}")
            raise RuntimeError(f"Failed to create transcription: {e}")
```

**Prevention:**
- Add comprehensive database operation logging
- Implement transaction verification checks
- Add database health checks to startup sequence
- Create integration tests that verify database persistence
- Monitor database connection pool status

**Testing the Fix:**
```bash
# Test with verification
curl -X POST "/audio/upload-and-transcribe" -F "file=@test.m4a"
# Check logs for "DEBUG: Transcription verified in database"

# Verify in database immediately
sqlite3 ./data/transcriptions.db "SELECT id, text FROM transcriptions WHERE created_at > datetime('now', '-1 minute');"
```

**Related Issues:**
- This may be related to SQLAlchemy session autocommit settings
- Database connection pooling issues with SQLite
- Entity mapping configuration problems
- ZenML context manager interference with database sessions

## 🤖 Task Runner Migration Notes

### Poethepoet Removal

The poethepoet task runner has been removed in favor of Makefile-based task management for better enterprise compatibility.

**Migration Notes:**
- All `poe <task>` commands have been replaced with `make <task>` equivalents
- Task configuration moved from `poe.tasks.toml` to `Makefile`
- Use `make help` to see available tasks

## 📦 Pydantic v2 Configuration

### Class-based Config Deprecation

Pydantic v2 has deprecated class-based Config in favor of ConfigDict.

**Old approach (deprecated):**
```python
class MyModel(BaseModel):
    class Config:
        validate_assignment = True
```

**New approach:**
```python
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
```

### Field Exclusion Pattern

For field exclusion, use the Annotated pattern with Field(exclude=True):

```python
from typing import Annotated, TypeVar
from pydantic import Field

T = TypeVar("T")
ExcludedField = Annotated[T, Field(exclude=True)]

class MyModel(BaseModel):
    visible_field: str
    hidden_field: ExcludedField[str] = None
```

## 🔄 Python Import Issues

### Module Import Path Conflict

When using `mypy`, you might encounter an error like:

```
Source file found twice under different module names: "models.DataWarehouseEntry" and "src.domain.models.DataWarehouseEntry"
```

This happens when mypy finds the same Python module imported via different paths.

**Causes:**
- Mixing absolute and relative imports
- Missing `__init__.py` files
- Inconsistent import patterns across the codebase

**Solutions:**

1. **Be consistent with import styles**
   - Prefer relative imports within the same package: 
     ```python
     # Good - for importing from same directory
     from .DataWarehouseEntry import DataWarehouseEntry
     ```
   - Use absolute imports for external modules:
     ```python
     # Good - for importing from different packages
     from src.another_package.module import Something
     ```

2. **Ensure `__init__.py` exists in all directories**
   - Add empty `__init__.py` files to all directories that should be Python packages:
     ```
     src/__init__.py
     src/domain/__init__.py
     src/domain/models/__init__.py
     src/infrastructure/__init__.py
     ```

3. **Avoid mixing import styles**
   - Don't import the same module using both relative and absolute paths in different files

### PYTHONPATH in Tests

When running pytest, you might encounter module import errors like this:

```
ModuleNotFoundError: No module named 'src'
```

**Causes:**
- Python's module system requires directories to be in the PYTHONPATH
- Tests run from a different working directory or context
- Poetry's isolation affects the Python path

**Solutions:**

1. **Update the pytest configuration in pyproject.toml**:
   ```toml
   [tool.pytest.ini_options]
   pythonpath = ["."]
   testpaths = ["src"]
   ```

2. **Create a conftest.py file** in the project root:
   ```python
   import sys
   from pathlib import Path
   
   # Add the project root to the Python path
   project_root = Path(__file__).parent.absolute()
   if str(project_root) not in sys.path:
       sys.path.insert(0, str(project_root))
   ```

3. **Update the test command** in Makefile:
   ```makefile
   test:
   	PYTHONPATH=$PYTHONPATH:. poetry run pytest src -v
   ```

These solutions ensure that the project root is in the Python path when running tests.

## 🔌 Supabase Client Type Issues

### Response Object Access

The Supabase Python client's response object has changed its interface in newer versions. Older code might try to access response values using dictionary-style notation which no longer works.

**Issue with dictionary access:**
```python
response = client.table("my_table").insert(data).execute()
if response.get("error"):  # TypeError: 'APIResponse' object is not subscriptable
    raise Exception(f"Error: {response['error']}")  # TypeError: 'APIResponse' object is not subscriptable
```

**Solution - Use attribute access:**
```python
response = client.table("my_table").insert(data).execute()
if hasattr(response, 'error') and response.error:
    raise Exception(f"Error: {response.error}")
```

When working with response data:
```python
# Safe way to check for response data
if response.data and len(response.data) > 0:
    # Access the first item
    first_item = response.data[0]
```

## ✅ Mypy Type Checking

### Test Function Return Types

When using strict mypy settings like `disallow_untyped_defs = true`, all functions including test functions require return type annotations.

**Issue:**
```python
src/domain/models/__tests__/test_DataWarehouseEntry.py:9: error: Function is missing a return type annotation [no-untyped-def]
src/domain/models/__tests__/test_DataWarehouseEntry.py:9: note: Use "-> None" if function does not return a value
```

**Solution:**
Add return type annotations to all test functions:
```python
def test_create_data_warehouse_entry() -> None:
    # Test code here
    assert True
```

## 📅 Datetime Handling

### datetime.utcnow() Deprecation

Python 3.11+ shows warnings about `datetime.utcnow()`, as it's being deprecated in favor of timezone-aware alternatives.

**Issue:**
```
DeprecationWarning: datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects with UTC (datetime.now(timezone.utc))
```

**Solution:**
```python
from datetime import datetime, timezone

# Instead of
now = datetime.utcnow()

# Use
now = datetime.now(timezone.utc)
```

For pydantic models:
```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

## 📏 Line Length Conflicts

### Black and Ruff Disagreement

Black and Ruff may sometimes disagree on line length and formatting, even with the same `line-length` setting.

**Solution:**

Ensure both tools have the same line length configuration:

```toml
[tool.black]
line-length = 120

[tool.ruff]
line-length = 120
```

And use the combined format-and-lint task to resolve conflicts:
```bash
poetry run poe format-and-lint
```

## 🗃️ Supabase Storage Issues

### Downloading Files from Supabase Storage

When downloading files from Supabase Storage, you might encounter a 400 Bad Request error:

```
Failed to download file from storage: 400 Client Error: Bad Request for url: http://localhost:54321/storage/v1/object/public/audio-files/...
```

**Causes:**
- The public URL from `get_public_url()` is not meant for direct downloads with authentication
- Missing authorization headers in the request
- Using the wrong URL format for downloading

**Solutions:**

1. **Use the storage3 client directly for downloads**
   ```python
   # Extract bucket and path from URL
   match = re.match(r'https?://[^/]+/storage/v1/object/public/([^/]+)/(.+)', file_path)
   bucket_name = match.group(1)
   object_path = match.group(2)
   
   # Create storage client with proper authentication
   storage_url = f"{settings.supabase_url}/storage/v1"
   headers = {
       "apiKey": settings.supabase_key,
       "Authorization": f"Bearer {settings.supabase_key}"
   }
   storage = create_storage_client(storage_url, headers, is_async=False)
   
   # Download the file directly using the storage client
   file_data = storage.from_(bucket_name).download(object_path)
   ```

2. **Add proper authentication headers if using HTTP requests**
   ```python
   # Extract bucket and path from URL
   match = re.match(r'https?://[^/]+/storage/v1/object/public/([^/]+)/(.+)', file_path)
   bucket_name = match.group(1)
   object_path = match.group(2)
   
   # Construct proper download URL
   download_url = f"{settings.supabase_url}/storage/v1/object/{bucket_name}/{object_path}"
   
   # Add necessary authorization headers
   headers = {
       "apiKey": settings.supabase_key,
       "Authorization": f"Bearer {settings.supabase_key}"
   }
   
   # Make the request
   response = requests.get(download_url, headers=headers)
   ```

3. **Add debug logging to troubleshoot Supabase storage issues**
   ```python
   logger.info(f"Extracted bucket: {bucket_name}, path: {object_path}")
   logger.info(f"Constructed download URL: {download_url}")
   logger.info(f"Making request with headers: {headers}")
   ```

These solutions ensure that file downloads from Supabase storage work correctly by using the proper authentication and URL format.

## 🌍 Environment Variable Inheritance Issues

### Poetry/Poe Tasks Not Loading Environment Variables

When using `poetry run poe <task>`, you might encounter issues where environment variables set in your shell or `.env` file are not being loaded, leading to errors like:

```
OpenAI transcription failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: your_ope************here.'
```

**Issue:**
- Poe tasks run in isolated environments that don't automatically inherit shell environment variables
- Tasks don't automatically load `.env` files unless explicitly configured
- This can cause applications to fall back to placeholder/default values instead of real configuration

**Symptoms:**
- API calls failing with placeholder API keys like "your_ope************here"
- Database connections using defaults (e.g., in-memory SQLite) instead of configured URLs
- Settings showing correct values when tested directly, but failing when run through Poe tasks

**Root Cause:**
Poe tasks by default only export variables explicitly defined in the task, like:
```toml
[tool.poe.tasks]
my-task = { shell = """
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
python -m uvicorn src.main:app --reload --port 8000
""" }
```

This task only exports `OBJC_DISABLE_INITIALIZE_FORK_SAFETY` but ignores other environment variables.

**Solutions:**

1. **Load .env file in Makefile tasks**
   ```makefile
   dev-start:
	# Load environment variables from .env file if it exists
	if [ -f .env ]; then \
	  echo "📋 Loading environment variables from .env file..."; \
	  export $(grep -v '^#' .env | xargs); \
	fi
	# Validate critical environment variables
	if [ -z "$$OPENAI_API_KEY" ]; then \
	  echo "⚠️  WARNING: OPENAI_API_KEY not set. Transcription may fail."; \
	else \
	  echo "✅ OPENAI_API_KEY loaded successfully"; \
	fi
	poetry run python -m uvicorn src.main:app --reload --port 8000
   ```

2. **Create environment validation helpers**
   ```bash
   # Check that critical environment variables are set
   if [ -z "$DATABASE_URL" ]; then
     echo "⚠️  WARNING: DATABASE_URL not set. Using default SQLite."
   else
     echo "✅ DATABASE_URL: $DATABASE_URL"
   fi
   ```

3. **Debug environment variables**
   Create a debug script to verify what's loaded:
   ```python
   # debug_settings.py
   import os
   from src.config.settings import get_settings
   
   print("=== Environment Variables ===")
   for key in sorted(os.environ.keys()):
       if "OPENAI" in key or "DATABASE" in key:
           value = os.environ[key]
           if "API_KEY" in key:
               print(f"{key}={value[:10]}...{value[-10:]}")
           else:
               print(f"{key}={value}")
   
   settings = get_settings()
   print(f"Loaded API Key: {settings.openai.api_key[:10]}...{settings.openai.api_key[-10:]}")
   ```

4. **Clear cached settings when troubleshooting**
   ```python
   # clear_cache.py
   from src.config.settings import get_settings
   
   # Clear the lru_cache 
   get_settings.cache_clear()
   print("✓ Settings cache cleared")
   ```

**Prevention:**
- Always include `.env` file loading in development tasks
- Add environment variable validation to catch missing values early
- Use consistent environment variable names across all configurations
- Test tasks in clean environments to ensure they work without inheriting shell state

**Testing the Fix:**
```bash
# Test that environment variables are loaded correctly
make dev-start

# Look for these success messages:
# ✅ OPENAI_API_KEY loaded successfully
# ✅ DATABASE_URL: sqlite:///./data/transcriptions.db
```

[↑ Back to Top](#-table-of-contents) 