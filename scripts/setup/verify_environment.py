#!/usr/bin/env python3
"""
Environment Verification Script

Verifies that the development environment is properly configured.
Checks for:
- Python version
- Poetry installation
- Docker availability
- Required files and directories
- Docker services status
- Python dependencies
"""

import subprocess
import sys
from pathlib import Path
from typing import Callable, List


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header() -> None:
    """Print the verification header."""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  IBCo Vallejo Console - Environment Verification{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print()


def print_check(name: str, passed: bool, message: str = "") -> None:
    """Print a check result."""
    status = f"{Colors.GREEN}✓{Colors.NC}" if passed else f"{Colors.RED}✗{Colors.NC}"
    print(f"{status} {name}", end="")
    if message:
        print(f" - {message}")
    else:
        print()


def check_python_version() -> tuple[bool, str]:
    """Verify Python version is 3.11+."""
    version = sys.version_info
    if version < (3, 11):
        return False, f"Python 3.11+ required (found {version.major}.{version.minor})"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_poetry_installation() -> tuple[bool, str]:
    """Verify Poetry is installed."""
    try:
        result = subprocess.run(
            ["poetry", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "Poetry not found"
    except FileNotFoundError:
        return False, "Poetry not installed"


def check_docker_installed() -> tuple[bool, str]:
    """Verify Docker is installed."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "Docker not found"
    except FileNotFoundError:
        return False, "Docker not installed"


def check_docker_running() -> tuple[bool, str]:
    """Verify Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "Docker daemon is running"
        return False, "Docker daemon not running"
    except Exception as e:
        return False, f"Error checking Docker: {e}"


def check_env_file() -> tuple[bool, str]:
    """Verify .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        return True, ".env file found"
    return False, ".env file not found (copy from .env.example)"


def check_data_directories() -> tuple[bool, str]:
    """Verify required data directories exist."""
    required_dirs = [
        "data/raw/cafr",
        "data/raw/calpers",
        "data/raw/state_controller",
        "data/processed",
        "data/archive",
        "data/samples",
    ]

    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)

    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, f"{len(required_dirs)} data directories found"


def check_src_structure() -> tuple[bool, str]:
    """Verify source code structure exists."""
    required_dirs = [
        "src/config",
        "src/database",
        "src/data_pipeline",
        "src/analytics",
        "src/api",
        "tests/unit",
        "tests/integration",
    ]

    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)

    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, f"{len(required_dirs)} source directories found"


def check_config_files() -> tuple[bool, str]:
    """Verify required configuration files exist."""
    required_files = [
        "pyproject.toml",
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        ".flake8",
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    return True, f"{len(required_files)} config files found"


def check_docker_services() -> tuple[bool, str]:
    """Check if Docker services are running."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            services = [s for s in result.stdout.strip().split("\n") if s]
            if services:
                return True, f"{len(services)} services running: {', '.join(services)}"
            return False, "No Docker services running (run: docker compose up -d)"
        return False, "Could not check Docker services"
    except Exception as e:
        return False, f"Error checking services: {e}"


def check_postgres_connection() -> tuple[bool, str]:
    """Check if PostgreSQL is accessible."""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "ibco"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "PostgreSQL is ready"
        return False, "PostgreSQL not ready"
    except subprocess.TimeoutExpired:
        return False, "PostgreSQL check timed out"
    except Exception as e:
        return False, f"Cannot check PostgreSQL: {e}"


def check_redis_connection() -> tuple[bool, str]:
    """Check if Redis is accessible."""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            return True, "Redis is ready"
        return False, "Redis not ready"
    except subprocess.TimeoutExpired:
        return False, "Redis check timed out"
    except Exception as e:
        return False, f"Cannot check Redis: {e}"


def check_git_hooks() -> tuple[bool, str]:
    """Check if git hooks are installed."""
    hook_path = Path(".git/hooks/pre-commit")
    if hook_path.exists() and hook_path.is_file():
        return True, "Git pre-commit hook installed"
    return False, "Git hooks not installed (run: bash scripts/setup/install_git_hooks.sh)"


def run_verification() -> int:
    """Run all verification checks and return exit code."""
    print_header()

    # Define all checks
    checks: List[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("Python Version", check_python_version),
        ("Poetry Installation", check_poetry_installation),
        ("Docker Installation", check_docker_installed),
        ("Docker Daemon", check_docker_running),
        ("Environment File", check_env_file),
        ("Configuration Files", check_config_files),
        ("Source Structure", check_src_structure),
        ("Data Directories", check_data_directories),
        ("Git Hooks", check_git_hooks),
        ("Docker Services", check_docker_services),
        ("PostgreSQL", check_postgres_connection),
        ("Redis", check_redis_connection),
    ]

    # Run all checks
    results = []
    for name, check_func in checks:
        try:
            passed, message = check_func()
            print_check(name, passed, message)
            results.append((name, passed, message))
        except Exception as e:
            print_check(name, False, f"Error: {e}")
            results.append((name, False, str(e)))

    # Print summary
    print()
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    success_rate = (passed_count / total_count) * 100

    if passed_count == total_count:
        print(f"{Colors.GREEN}✓ All checks passed! ({passed_count}/{total_count}){Colors.NC}")
        print()
        print("Your development environment is ready!")
        print()
        print("Next steps:")
        print("  1. Review .env configuration")
        print("  2. Initialize database: poetry run alembic upgrade head")
        print("  3. Run tests: poetry run pytest")
        print("  4. Start API: poetry run uvicorn src.api.main:app --reload")
        return 0
    else:
        failed_count = total_count - passed_count
        print(f"{Colors.RED}✗ {failed_count} check(s) failed ({passed_count}/{total_count} passed){Colors.NC}")
        print()
        print("Failed checks:")
        for name, passed, message in results:
            if not passed:
                print(f"  • {name}: {message}")
        print()
        print("Please fix the issues above and run this script again.")
        return 1


if __name__ == "__main__":
    exit_code = run_verification()
    sys.exit(exit_code)
