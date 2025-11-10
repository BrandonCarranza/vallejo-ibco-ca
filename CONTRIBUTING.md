# Contributing to IBCo Vallejo Console

Thank you for your interest in contributing to IBCo Vallejo Console! This project aims to bring transparency to municipal finances, and we welcome contributions from developers, data analysts, civic enthusiasts, and concerned citizens.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Data Errors](#reporting-data-errors)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
  - [Improving Documentation](#improving-documentation)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Data Errors

Data accuracy is our highest priority. If you find an error:

1. **Email us immediately**: data@ibco-ca.us
2. **Provide details**:
   - What data point is incorrect (specific field, year, value)
   - What you believe the correct value should be
   - Source document/citation for the correction
   - Your contact information (optional but helpful)

3. **What happens next**:
   - We will investigate within 48 hours
   - If confirmed, we'll publish a correction
   - Historical snapshots will note the correction
   - We'll credit you (unless you prefer to remain anonymous)

**Critical**: Do not create GitHub issues for data errors. Email us directly to ensure rapid response.

### Suggesting Features

We welcome feature suggestions that advance our mission of fiscal transparency.

**Before suggesting**:
- Check existing GitHub issues to avoid duplicates
- Consider whether this aligns with our core mission
- Think about implementation complexity vs. value

**How to suggest**:
1. Open a GitHub issue with the "Feature Request" template
2. Describe the problem this feature would solve
3. Outline your proposed solution
4. Consider potential limitations or concerns

### Contributing Code

We accept code contributions that:
- Improve data quality or validation
- Enhance API functionality
- Add useful analytics or visualizations
- Improve performance or reliability
- Fix bugs
- Improve developer experience

**Areas where we especially need help**:
- Data extraction from PDF CAFRs
- Additional data validation checks
- Performance optimization for large datasets
- Accessibility improvements
- Mobile-responsive design

### Improving Documentation

Documentation is critical for a transparency project. Contributions welcome for:
- Code documentation and docstrings
- Architecture documentation
- User guides and tutorials
- Methodology explanations
- Data source guides

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Docker and Docker Compose
- Git
- PostgreSQL (or use Docker)

### Initial Setup

1. **Clone the repository**
```bash
git clone https://github.com/ibco-ca/vallejo-ibco-ca.git
cd vallejo-ibco-ca
```

2. **Install dependencies**
```bash
poetry install
poetry shell
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your local settings
```

4. **Start services with Docker**
```bash
docker-compose up -d postgres redis
```

5. **Initialize database**
```bash
poetry run alembic upgrade head
poetry run python scripts/setup/seed_database.py
```

6. **Run tests to verify setup**
```bash
poetry run pytest
```

7. **Start the development server**
```bash
poetry run uvicorn src.api.main:app --reload
```

Visit http://localhost:8000/docs for the API documentation.

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/your-feature-name`: Your feature branch
- `fix/bug-description`: Bug fix branches

### Workflow Steps

1. **Create a branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write code following our style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run linting
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: Add descriptive commit message"
```

Use [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

5. **Push and create a Pull Request**
```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub from your branch to `develop`.

## Coding Standards

### Python Style Guide

- **PEP 8**: Follow Python's official style guide
- **Black**: Use Black for code formatting (line length: 100)
- **isort**: Use isort for import sorting
- **Type hints**: Add type hints to all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions/classes

### Example

```python
from typing import Optional
from datetime import date

def calculate_fund_balance_ratio(
    fund_balance: float,
    expenditures: float,
    fiscal_year: date,
) -> Optional[float]:
    """Calculate the fund balance ratio for a given fiscal year.

    Args:
        fund_balance: Total general fund balance in dollars
        expenditures: Total general fund expenditures in dollars
        fiscal_year: The fiscal year end date

    Returns:
        Fund balance ratio as a percentage (0-100), or None if
        expenditures is zero.

    Raises:
        ValueError: If fund_balance or expenditures is negative
    """
    if fund_balance < 0 or expenditures < 0:
        raise ValueError("Financial values cannot be negative")

    if expenditures == 0:
        return None

    return (fund_balance / expenditures) * 100
```

### Code Organization

- Keep functions small and focused (< 50 lines)
- Use descriptive variable names (no single-letter vars except loop counters)
- Avoid deep nesting (max 3 levels)
- Extract complex logic into separate functions
- Comment "why", not "what"

### Database Guidelines

- Always use SQLAlchemy ORM (no raw SQL in application code)
- All schema changes via Alembic migrations
- Include rollback logic in migrations
- Add indexes for foreign keys and frequently queried fields
- Use appropriate constraints (NOT NULL, UNIQUE, CHECK)

## Testing Requirements

### Test Coverage Requirements

- **Minimum coverage**: 80% for new code
- **Critical paths**: 100% coverage required for:
  - Data validation logic
  - Risk scoring calculations
  - Financial calculations
  - Data transformations

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1s per test)

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use test database
   - Test API endpoints

3. **Fixtures** (`tests/fixtures/`)
   - Sample data for testing
   - Realistic test scenarios

### Writing Good Tests

```python
import pytest
from src.analytics.risk_scoring.indicators import calculate_fund_balance_ratio

def test_fund_balance_ratio_normal_case():
    """Test fund balance ratio calculation with typical values."""
    ratio = calculate_fund_balance_ratio(
        fund_balance=10_000_000,
        expenditures=50_000_000,
    )
    assert ratio == pytest.approx(20.0)

def test_fund_balance_ratio_zero_expenditures():
    """Test that zero expenditures returns None."""
    ratio = calculate_fund_balance_ratio(
        fund_balance=10_000_000,
        expenditures=0,
    )
    assert ratio is None

def test_fund_balance_ratio_negative_values():
    """Test that negative values raise ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_fund_balance_ratio(
            fund_balance=-1000,
            expenditures=50_000_000,
        )
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted with Black and isort
- [ ] Linting passes (flake8, mypy)
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow Conventional Commits format
- [ ] Branch is up-to-date with develop

### PR Description Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you added/updated

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated checks**: CI/CD will run tests and linting
2. **Code review**: At least one maintainer will review
3. **Feedback**: Address any comments or requested changes
4. **Approval**: Once approved, a maintainer will merge

### Review Criteria

Reviewers will check:
- Code quality and maintainability
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations (especially for data handling)
- Alignment with project goals

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Data corrections**: Email data@ibco-ca.us
- **Security issues**: Email security@ibco-ca.us (PGP key available)

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

Thank you for contributing to government transparency!
