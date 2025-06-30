"""
Startup banner and configuration display module.

This module provides functions to display the system configuration
in a beautiful, readable format during application startup.
"""

import logging

from src.agent_project.config.settings import AppSettings


def create_startup_banner(settings: AppSettings) -> str:
    """
    Create a beautiful startup banner with system configuration.

    Args:
        settings: Application settings instance

    Returns:
        str: Formatted startup banner
    """
    info = settings.get_startup_info()

    # Determine database display name
    db_type = info["database"]["type"]
    db_url = info["database"]["url"]
    if db_type == "SQLite":
        db_display = f"SQLite ({db_url})"
    else:
        # Hide credentials but show host/database
        db_display = f"PostgreSQL ({db_url})"

    # Determine agent configuration
    agents_configured = "✅ Configured" if info["agents"]["openai_configured"] else "❌ Not configured"

    # Determine storage display
    storage_backend = info["storage"]["backend"]
    storage_path = info["storage"]["path"]
    max_size = info["storage"]["max_file_size_mb"]

    if storage_backend == "local":
        storage_display = f"Local FileSystem ({storage_path})"
    else:
        storage_display = f"Supabase Storage ({storage_path})"

    # API URL
    api_url = f"http://{info['api']['host']}:{info['api']['port']}"
    if info["api"]["host"] == "0.0.0.0":
        api_url = f"http://localhost:{info['api']['port']}"

    banner = f"""
🤖  Agent Template v{settings.api.version}
=====================================
Database: {db_display}
OpenAI Agents: {agents_configured}
Storage: {storage_display} (max: {max_size}MB)
Environment: {info['environment']}
API: {api_url}
Log Level: {info['api']['log_level']}
=====================================
"""
    return banner


def print_startup_banner(settings: AppSettings) -> None:
    """
    Print the startup banner to console.

    Args:
        settings: Application settings instance
    """
    banner = create_startup_banner(settings)
    print(banner)


def log_startup_info(settings: AppSettings, logger: logging.Logger) -> None:
    """
    Log detailed startup information for debugging.

    Args:
        settings: Application settings instance
        logger: Logger instance to use
    """
    info = settings.get_startup_info()

    logger.info("Application startup configuration:")
    logger.info(f"Environment: {info['environment']}")
    logger.info(f"API: {info['api']['host']}:{info['api']['port']} (log_level={info['api']['log_level']})")

    logger.info(f"Database: {info['database']['type']}")
    logger.info(f"Database URL: {info['database']['url']}")
    logger.info(f"Auto-migrate: {info['database']['auto_migrate']}")

    logger.info(f"Storage backend: {info['storage']['backend']}")
    logger.info(f"Storage path: {info['storage']['path']}")
    logger.info(f"Max file size: {info['storage']['max_file_size_mb']}MB")

    logger.info(f"OpenAI configured: {info['agents']['openai_configured']}")


def log_component_status(settings: AppSettings, logger: logging.Logger) -> None:
    """
    Log the status of each major component.

    Args:
        settings: Application settings instance
        logger: Logger instance to use
    """
    logger.info("Component initialization status:")

    # Database component
    try:
        settings.validate_configuration()
        logger.info("✓ Configuration validation passed")
    except Exception as e:
        logger.error(f"✗ Configuration validation failed: {e}")
        raise

    # Storage component
    if settings.storage.backend.value == "local":
        try:
            from pathlib import Path

            Path(settings.storage.local_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Local storage directory ready: {settings.storage.local_path}")
        except Exception as e:
            logger.error(f"✗ Local storage setup failed: {e}")
            raise
    else:
        logger.info("✓ Supabase storage configured")

    # Database component
    if settings.database.url.startswith("sqlite:"):
        try:
            from pathlib import Path

            db_path = settings.database.url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            logger.info("✓ SQLite database directory ready")
        except Exception as e:
            logger.error(f"✗ SQLite setup failed: {e}")
            raise
    else:
        logger.info("✓ PostgreSQL database configured")

    # Agent/OpenAI component
    if not settings.openai.api_key or settings.openai.api_key == "your-api-key-here":
        logger.warning("⚠ OpenAI API key not configured - agent functionality will be limited")
    else:
        logger.info("✓ OpenAI API key configured - agents ready")
