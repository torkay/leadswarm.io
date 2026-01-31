# Testing Patterns

**Analysis Date:** 2026-02-01

## Test Framework

**Runner:**
- pytest (specified in `pyproject.toml`)
- pytest-asyncio for async test support
- pytest-cov for coverage reporting

**Assertion Library:**
- pytest built-in assert statements
- Direct assertions: `assert condition`
- Comparison: `assert value == expected`

**Run Commands:**
```bash
make test                    # Run all tests (pytest tests/ -v --tb=short)
make test-cov                # Run with coverage (--cov=prospect --cov-report=html)
make test-integration        # Run integration tests only (-m integration)
pytest tests/test_web.py     # Single file
pytest tests/ -k "spam"      # Run tests matching pattern
```

## Test File Organization

**Location:**
- All tests in `tests/` directory at project root
- Not co-located with source files

**Naming:**
- `test_*.py` for all test files
- No distinction in filename between unit/integration

**Structure:**
```
tests/
├── test_enrichment.py      # Email/contact extraction tests
├── test_web.py             # FastAPI endpoint tests
├── test_search_depth.py    # Location expansion, search logic
├── test_data_accuracy.py   # Domain normalization tests
├── test_sheets.py          # Google Sheets integration
└── test_serpapi.py         # SerpAPI client tests
```

## Test Structure

**Suite Organization:**
```python
import pytest
from prospect.validation import is_spam_email

class TestSpamEmailFiltering:
    """Tests for spam email detection."""

    def test_error_tracking_email_is_spam(self):
        """Error tracking emails should be detected as spam."""
        assert is_spam_email("abc123@error-tracking.reddit.com") is True

    def test_regular_email_not_spam(self):
        """Regular business emails should not be spam."""
        assert is_spam_email("contact@business.com") is False
```

**Patterns:**
- Class-based organization by feature (`TestSpamEmailFiltering`, `TestWebPages`)
- Descriptive docstrings for each test
- One assertion focus per test (multiple expects OK)
- beforeEach equivalent: `@pytest.fixture`

## Mocking

**Framework:**
- pytest built-in mocking with `unittest.mock`
- `@pytest.fixture` for test setup

**Patterns:**
```python
@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient
    app = create_app()
    return TestClient(app)

def test_homepage_loads(client):
    """Homepage should return 200."""
    response = client.get("/")
    assert response.status_code == 200
```

**What to Mock:**
- External API calls (SerpAPI, Stripe)
- File system operations
- Network requests

**What NOT to Mock:**
- Internal pure functions
- Validation utilities
- Data models

## Fixtures and Factories

**Test Data:**
```python
# Inline fixtures for simple cases
def test_normalize_domain():
    assert normalize_domain("https://www.example.com/page") == "example.com"

# pytest fixtures for complex setup
@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient
    app = create_app()
    return TestClient(app)
```

**Location:**
- Simple fixtures: inline in test file
- Shared fixtures: `conftest.py` (if needed)
- No separate fixtures directory currently

## Coverage

**Requirements:**
- No enforced coverage target
- Coverage tracked for awareness
- Focus on critical paths (validation, scoring, API endpoints)

**Configuration:**
- pytest-cov via `--cov=prospect`
- Excludes: test files, config files

**View Coverage:**
```bash
make test-cov
open coverage/index.html
```

## Test Types

**Unit Tests:**
- Test single function in isolation
- Examples: `test_enrichment.py` (spam detection), `test_data_accuracy.py` (normalization)
- Fast: each test <100ms
- Mock external dependencies

**Integration Tests:**
- Test multiple modules together
- Marked with `@pytest.mark.integration`
- Examples: `test_web.py` (FastAPI endpoints)
- Use TestClient for HTTP testing

**E2E Tests:**
- Not currently implemented
- CLI tested manually

## Common Patterns

**Async Testing:**
```python
# pytest-asyncio auto mode enabled in pyproject.toml
pytest_plugins = ('pytest_asyncio',)

async def test_async_function():
    result = await async_operation()
    assert result == expected
```

**Error Testing:**
```python
def test_invalid_input_raises():
    """Should raise error on invalid input."""
    with pytest.raises(ValueError):
        validate_input(None)
```

**Parametrized Tests:**
```python
@pytest.mark.parametrize("input,expected", [
    ("https://example.com", "example.com"),
    ("http://www.test.org/page", "test.org"),
])
def test_normalize_domain(input, expected):
    assert normalize_domain(input) == expected
```

**FastAPI Testing:**
```python
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Prospect" in response.text
```

## Test Markers

**Available Markers** (from `pyproject.toml`):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests"
]
```

**Usage:**
```bash
pytest -m integration          # Run only integration tests
pytest -m "not integration"    # Skip integration tests
```

## Development Workflow

**Pre-commit:**
```bash
black prospect/ tests/
ruff check prospect/ tests/
pytest tests/ -v
```

**CI Pattern:**
- Run lint checks first
- Run tests with coverage
- Block on failures

---

*Testing analysis: 2026-02-01*
*Update when test patterns change*
