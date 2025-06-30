# 🐛 Issue Tracker - ZenML Audio Transcription Service

## 🚨 Critical Issues

### Issue #001: API Error Handling
- **Status**: 🔴 Open
- **Priority**: High
- **Description**: OpenAI API errors (e.g., 400 Bad Request for invalid file format) are currently saved as transcriptions with error text. While this prevents data loss, it's not ideal UX.
- **Current Behavior**: 
  - Error transcriptions are saved to DB (good for data integrity)
  - Status shows "completed" even for errors (confusing)
  - Error text is stored in transcription.text field
- **Desired Behavior**:
  - Status should be "failed" for API errors
  - Separate error field for error details
  - Better error classification (client vs server errors)
  - Retry mechanism for transient errors
- **Files Affected**: `src/domain/transcription/transcription_service_openai.py`

### Issue #002: Audio Download Endpoint Missing
- **Status**: 🔴 Open  
- **Priority**: High
- **Description**: Transcription responses now include `/audio/{audio_id}/download` endpoint but this route doesn't exist
- **Current Behavior**: 
  - 404 error when accessing download endpoint
  - Example failing URL: `http://localhost:8000/audio/67c2958e-bf0f-40e9-a357-ac197fcec7a9/download`
  - Returns: `{"detail":"Not Found"}`
- **Desired Behavior**: Implement audio file download endpoint that serves the original audio file
- **Files Affected**: `src/routes/audio_routes.py`

## 🔮 Enhancement Ideas

### Issue #003: Event-Driven Architecture  
- **Status**: 🔵 Future
- **Priority**: Medium
- **Description**: Add event system for transcription lifecycle events
- **Benefits**:
  - Better monitoring and observability
  - Webhook notifications
  - Audit trail
  - Integration with external systems
- **Events to implement**:
  - `TranscriptionStarted`
  - `TranscriptionCompleted`
  - `TranscriptionFailed`
  - `AudioFileUploaded`
  - `AudioFileDeleted`

### Issue #004: Improved Logging and Monitoring
- **Status**: 🔵 Future
- **Priority**: Medium  
- **Description**: Enhanced logging for production monitoring
- **Features**:
  - Structured logging with correlation IDs
  - Performance metrics (processing time, file size, etc.)
  - Error classification and alerting
  - Health check improvements
  - Metrics endpoint for Prometheus/Grafana

### Issue #005: Segments Support
- **Status**: 🔵 Future
- **Priority**: Low
- **Description**: Currently segments are empty arrays. Could implement:
  - Timestamp-based segmentation
  - Speaker diarization
  - Word-level timestamps
  - Sentence/paragraph breaks

### Issue #006: Centralized Logging with LogGuru
- **Status**: 🔵 Future
- **Priority**: Medium
- **Description**: Standardize all logging through a centralized LogGuru logger instead of scattered print statements
- **Current Behavior**: 
  - Mix of `print()` statements and standard `logging` module usage
  - Inconsistent log formatting and levels
  - Difficult to control logging output in production
- **Desired Behavior**:
  - All logging goes through LogGuru for consistent formatting
  - Configurable log levels and outputs
  - Structured logging with context
  - Easy log filtering and searching
- **Files Affected**: 
  - `src/domain/transcription/transcription_service_local.py` (has multiple print statements)
  - All other service files with logging
  - Add LogGuru configuration module

### Issue #007: Domain-Infrastructure Separation (DDD Architecture)
- **Status**: 🔵 Future
- **Priority**: High
- **Description**: Domain layer contains infrastructure concerns, violating DDD principles
- **Current Behavior**: 
  - Domain services mix business logic with infrastructure concerns
  - Domain layer is not pure - contains database access, file I/O, external dependencies
  - Tight coupling between domain and infrastructure layers
- **Desired Behavior**:
  - Pure domain layer with only business logic and domain entities
  - Infrastructure concerns moved to infrastructure layer
  - Dependency injection for external services
  - Domain services focus solely on business rules
- **Files Affected**: 
  - `src/domain/` (various subdirectories contain mixed concerns)
  - Need architectural refactoring across domain services
  - Create proper interfaces and move implementations to infrastructure layer

### Issue #008: Prevent Mock Services in Production
- **Status**: 🔵 Future
- **Priority**: High
- **Description**: Mock services can currently run in production environments, which is unsafe
- **Current Behavior**: 
  - Mock services (e.g., MockWhisperTranscriptionService) can be used in any environment
  - No environment-based service selection validation
  - Risk of accidentally using mocks in production
- **Desired Behavior**:
  - Mock services only allowed when `TESTING=true` environment variable is set
  - Production environments must use real service implementations
  - Clear error messages when trying to use mocks in non-testing environments
  - Environment validation in service factory/dependency injection
- **Files Affected**: 
  - `src/domain/transcription/transcription_service_mock.py`
  - Service factory/configuration classes
  - Environment configuration validation

### Issue #009: Service Fallback Mechanisms
- **Status**: 🔵 Future
- **Priority**: Medium
- **Description**: Implement graceful fallback when primary services fail
- **Current Behavior**: 
  - Single point of failure for transcription services
  - No automatic fallback when services are unavailable
  - Limited error recovery options
- **Desired Behavior**:
  - Fallback chain: OpenAI → Local Whisper → Graceful degradation
  - Automatic retry with exponential backoff
  - Circuit breaker pattern for failing services
  - Graceful degradation with partial functionality
  - Health checks for service availability
- **Benefits**:
  - Improved reliability and uptime
  - Better user experience during outages
  - Automatic recovery from transient failures
- **Files Affected**: 
  - Service factory/orchestrator classes
  - Transcription service interfaces
  - Health check endpoints

### Issue #010: Missing Application Logs in Development Mode
- **Status**: 🔴 Open
- **Priority**: High
- **Description**: Application logs are not visible when running `make dev-start`
- **Current Behavior**: 
  - Server startup logs show correctly
  - Application runtime logs (API requests, transcription processing, etc.) are not displayed
  - Only shows "🔄 Services running. Press Ctrl+C to stop..." after startup
  - Difficult to debug issues during development
- **Desired Behavior**:
  - All application logs should be visible in real-time during development
  - Include API request logs, transcription processing logs, error logs
  - Maintain log level configuration (DEBUG/INFO/ERROR)
  - Preserve log formatting and colors
- **Impact**: Poor developer experience, difficult debugging
- **Files Affected**: 
  - `scripts/start_services.py`
  - FastAPI server startup configuration
  - Logging configuration
  - Uvicorn server settings

### Issue #011: Comprehensive Analytics and Performance Monitoring
- **Status**: 🔵 Future
- **Priority**: Medium
- **Description**: Implement comprehensive timing, analytics, and performance monitoring system
- **Current Behavior**: 
  - Limited performance visibility
  - No systematic function timing
  - Basic metrics only in transcription metadata
  - No centralized analytics collection
- **Desired Behavior**:
  - **Function Timing**: Decorator-based timing for all critical functions
  - **Event System**: Track important business events to analytics database
  - **Performance Metrics**: CPU, memory, I/O, processing times
  - **Analytics Dashboard**: Visualize performance trends and bottlenecks
  - **Optimization Insights**: Identify slowest functions and optimization opportunities
- **Features to Implement**:
  - Performance decorators (`@time_it`, `@monitor_performance`)
  - Event logging system for business events
  - Analytics database (separate from operational data)
  - Metrics collection and aggregation
  - Performance dashboards and alerts
  - Benchmarking and regression detection
- **Benefits**:
  - Data-driven optimization decisions
  - Early detection of performance regressions
  - Understanding system bottlenecks
  - Better capacity planning
- **Files Affected**: 
  - New analytics module/package
  - Performance monitoring decorators
  - Event system infrastructure
  - Analytics database schema
  - Dashboard/visualization components

## ✅ Completed Issues

### Issue #C001: UTF-8 Serialization Error
- **Status**: ✅ Completed (2025-06-05)
- **Description**: ZenML was trying to serialize AudioFile entities with binary content as UTF-8
- **Solution**: Pass audio_id instead of AudioFile entity to ZenML pipelines
- **Files Changed**: `src/routes/audio_routes.py`

### Issue #C002: Error Transcriptions Not Persisted  
- **Status**: ✅ Completed (2025-06-05)
- **Description**: OpenAI API errors were creating transcriptions but not saving them to database
- **Solution**: Added `self.transcription_repository.create(error_transcription)` to error handling
- **Files Changed**: `src/domain/transcription/transcription_service_openai.py`

### Issue #C003: ZenML Configuration  
- **Status**: ✅ Completed (2025-06-05)
- **Description**: ZenML store type was "sqlite" but should be "sql"
- **Solution**: Updated constants and environment variables
- **Files Changed**: `src/config/constants.py`

---

## 📋 How to Add Issues

1. **Critical Issues**: Need immediate attention, blocking production use
2. **Enhancement Ideas**: Future improvements, nice-to-have features  
3. **Completed Issues**: Moved here when resolved

### Issue Template:
```markdown
### Issue #XXX: [Title]
- **Status**: 🔴 Open / 🔵 Future / ✅ Completed
- **Priority**: High / Medium / Low
- **Description**: Brief description
- **Current Behavior**: What happens now
- **Desired Behavior**: What should happen
- **Files Affected**: List of files
``` 