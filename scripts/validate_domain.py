#!/usr/bin/env python3
"""
Domain Layer Purity Validator

This script validates that domain entities remain pure Python without framework dependencies.
Domain-Driven Design requires the domain layer to be infrastructure-agnostic.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def get_forbidden_imports() -> List[str]:
    """Get list of forbidden import prefixes for domain entities."""
    return [
        "sqlalchemy",
        "fastapi",
        "flask",
        "django",
        "requests",
        "httpx",
        "aiohttp",
        "redis",
        "psycopg2",
        "mysql",
        "sqlite3",  # Should use repository pattern instead
    ]


def get_allowed_imports() -> List[str]:
    """Get list of explicitly allowed imports for domain entities."""
    return [
        "typing",
        "dataclasses",
        "pydantic",
        "enum",
        "datetime",
        "uuid",
        "abc",
        "functools",
        "operator",
        "collections",
        "itertools",
    ]


def check_file_purity(file_path: Path) -> List[str]:
    """Check a single Python file for forbidden imports."""
    violations = []
    forbidden = get_forbidden_imports()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(fb) for fb in forbidden):
                        violations.append(f"Direct import: {alias.name}")

            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module.startswith(fb) for fb in forbidden):
                    violations.append(f"Import from: {node.module}")

    except Exception as e:
        violations.append(f"Parse error: {e}")

    return violations


def validate_domain_entities() -> Tuple[bool, List[str]]:
    """Validate all domain entity files for purity."""
    domain_path = Path("src/agent_project/domain/entities")

    if not domain_path.exists():
        return False, [f"Domain entities path not found: {domain_path}"]

    all_violations = []

    for py_file in domain_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        violations = check_file_purity(py_file)
        if violations:
            relative_path = py_file.relative_to(Path.cwd())
            for violation in violations:
                all_violations.append(f"{relative_path}: {violation}")

    return len(all_violations) == 0, all_violations


def main():
    """Main validation entry point."""
    print("🧪 Validating domain layer purity...")
    print("Checking domain entities for framework dependencies...")

    is_pure, violations = validate_domain_entities()

    if is_pure:
        print("✅ Domain entities are pure Python")
        print("   - No forbidden framework dependencies found")
        print("   - Domain layer maintains infrastructure independence")
        return 0
    else:
        print("❌ Domain purity violations found:")
        for violation in violations:
            print(f"   - {violation}")
        print()
        print("💡 Domain entities should only depend on:")
        print("   - Standard library modules (typing, dataclasses, datetime, etc.)")
        print("   - Pydantic for validation")
        print("   - Other domain entities")
        print("   - No framework dependencies (SQLAlchemy, FastAPI, etc.)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
