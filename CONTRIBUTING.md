# Contributing to Prospect Command Center

Thank you for your interest in contributing!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -e ".[dev]"`
5. Copy `.env.example` to `.env` and add your SerpAPI key

## Code Style

- Use [Black](https://black.readthedocs.io/) for formatting
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Write docstrings for all public functions
- Add type hints where practical

```bash
# Format
black prospect/ tests/

# Lint
ruff check prospect/ tests/
```

## Testing

All changes must include tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=prospect --cov-report=html

# Run specific test
pytest tests/test_scoring.py -v
```

## Pull Request Process

1. Create a branch from `beta`: `git checkout -b feature/my-feature beta`
2. Make your changes
3. Add/update tests
4. Run tests and linting
5. Commit with descriptive message
6. Push and create PR to `beta` branch

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new scoring algorithm
fix: correct phone number validation
docs: update API documentation
chore: bump dependencies
test: add tests for campaign endpoints
```

## Branch Strategy

| Branch | Purpose | Deployed |
|--------|---------|----------|
| `main` | Production releases | Railway (auto) |
| `beta` | Development | - |

## Questions?

Open an issue or email tor@sortedsystems.com
