# Testing Guide - MCP Servers

## Quick Reference

```bash
# Run all tests
./venv/bin/pytest

# Run tests with coverage
./venv/bin/pytest --cov=src/mcp_servers --cov-report=term-missing

# Run specific test file
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py

# Run specific test function
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py::test_audio_config_audio_file

# Run with verbose output
./venv/bin/pytest -v

# Run only unit tests
./venv/bin/pytest -m unit

# Run only integration tests
./venv/bin/pytest -m integration

# Watch mode (rerun on file changes - requires pytest-watch)
./venv/bin/ptw
```

---

## Setup

### Prerequisites

```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio pytest-cov
```

### Configuration

The project uses `pytest.ini` for configuration:

```ini
[pytest]
pythonpath = .              # Adds project root to Python path
testpaths = tests           # Where to look for tests
addopts = -v --strict-markers --tb=short
```

This means you can import from `src` in tests:
```python
from src.mcp_servers.first_crack_detection.models import AudioConfig
```

---

## Running Tests

### All Tests

```bash
# From project root
./venv/bin/pytest

# Or with activated venv
source venv/bin/activate
pytest
```

### First Crack Detection MCP Server

```bash
# All tests for first crack detection
./venv/bin/pytest tests/mcp_servers/first_crack_detection/

# Only unit tests
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/

# Only integration tests
./venv/bin/pytest tests/mcp_servers/first_crack_detection/integration/
```

### Specific Test Files

```bash
# Models tests
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py

# Session manager tests (when implemented)
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_session_manager.py

# Audio devices tests (when implemented)
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_audio_devices.py
```

### Specific Test Functions

```bash
# Single test
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py::test_audio_config_audio_file

# Multiple tests matching pattern
./venv/bin/pytest -k "audio_config"
```

---

## Test Markers

Mark tests with decorators:

```python
import pytest

@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

Run by marker:

```bash
# Only unit tests
./venv/bin/pytest -m unit

# Only integration tests
./venv/bin/pytest -m integration

# Skip slow tests
./venv/bin/pytest -m "not slow"
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
./venv/bin/pytest --cov=src/mcp_servers --cov-report=term-missing

# HTML report (opens in browser)
./venv/bin/pytest --cov=src/mcp_servers --cov-report=html
open htmlcov/index.html

# XML report (for CI)
./venv/bin/pytest --cov=src/mcp_servers --cov-report=xml
```

### Coverage for Specific Module

```bash
# Only first_crack_detection coverage
./venv/bin/pytest \
  tests/mcp_servers/first_crack_detection/ \
  --cov=src/mcp_servers/first_crack_detection \
  --cov-report=term-missing
```

### Target Coverage

We aim for **>80% test coverage** on all new code.

---

## TDD Workflow

### Red-Green-Refactor Cycle

**1. 🔴 RED - Write Failing Test**

```bash
# Write test first in tests/mcp_servers/first_crack_detection/unit/test_models.py

# Run and watch it fail
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py::test_new_feature -v
```

**2. 🟢 GREEN - Make It Pass**

```bash
# Implement minimal code in src/mcp_servers/first_crack_detection/models.py

# Run and watch it pass
./venv/bin/pytest tests/mcp_servers/first_crack_detection/unit/test_models.py::test_new_feature -v
```

**3. 🔵 REFACTOR - Clean Up**

```bash
# Improve code quality

# Run ALL tests to ensure nothing broke
./venv/bin/pytest tests/mcp_servers/first_crack_detection/
```

**4. ✅ VERIFY - Final Check**

```bash
# Run full test suite with coverage
./venv/bin/pytest --cov=src/mcp_servers --cov-report=term-missing
```

---

## Debugging Tests

### Verbose Output

```bash
# Show print statements
./venv/bin/pytest -s

# Very verbose
./venv/bin/pytest -vv

# Show local variables on failure
./venv/bin/pytest -l
```

### Drop into Debugger on Failure

```bash
# Use pdb
./venv/bin/pytest --pdb

# Stop on first failure
./venv/bin/pytest -x --pdb
```

### Run Last Failed Tests

```bash
# Only rerun tests that failed last time
./venv/bin/pytest --lf

# Run failed first, then others
./venv/bin/pytest --ff
```

---

## Writing Tests

### Test File Structure

```
tests/mcp_servers/first_crack_detection/
├── unit/
│   ├── test_models.py              # Pydantic models
│   ├── test_session_manager.py     # Session management
│   ├── test_audio_devices.py       # Audio device discovery
│   ├── test_config.py              # Configuration
│   └── test_utils.py               # Utilities
└── integration/
    └── test_mcp_integration.py     # End-to-end tests
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

```python
# Good
def test_audio_config_validates_file_path():
    pass

# Bad
def validate_file_path_test():
    pass
```

### Fixtures

Create reusable test fixtures in `conftest.py`:

```python
# tests/mcp_servers/first_crack_detection/conftest.py
import pytest

@pytest.fixture
def sample_audio_config():
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    return AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="/path/to/test.wav"
    )

@pytest.fixture
def mock_detector():
    from unittest.mock import Mock
    return Mock()
```

Use in tests:

```python
def test_something(sample_audio_config, mock_detector):
    # Use fixtures
    assert sample_audio_config.audio_source_type == "audio_file"
```

---

## Continuous Testing

### Watch Mode (Auto-rerun)

Install pytest-watch:

```bash
pip install pytest-watch
```

Watch and rerun on changes:

```bash
# Watch all tests
./venv/bin/ptw

# Watch specific directory
./venv/bin/ptw tests/mcp_servers/first_crack_detection/unit/

# With coverage
./venv/bin/ptw -- --cov=src/mcp_servers
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=src/mcp_servers --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Common Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**: 
- Ensure `pytest.ini` exists with `pythonpath = .`
- Or run with: `PYTHONPATH=. pytest`

### Fixture Not Found

**Problem**: `fixture 'mock_detector' not found`

**Solution**: 
- Check `conftest.py` exists in test directory
- Ensure fixture is defined correctly

### Test Collection Errors

**Problem**: `ERROR collecting tests`

**Solution**:
```bash
# Verbose collection to see the issue
./venv/bin/pytest --collect-only -v
```

---

## Performance

### Parallel Execution

Install pytest-xdist:

```bash
pip install pytest-xdist
```

Run in parallel:

```bash
# Auto-detect CPU count
./venv/bin/pytest -n auto

# Specific number of workers
./venv/bin/pytest -n 4
```

### Profiling Slow Tests

```bash
# Show 10 slowest tests
./venv/bin/pytest --durations=10
```

---

## Best Practices

### ✅ Do

- Write tests first (TDD)
- Test one thing per test function
- Use descriptive test names
- Use fixtures for common setup
- Mock external dependencies
- Aim for >80% coverage
- Run tests before committing

### ❌ Don't

- Test implementation details
- Write tests that depend on each other
- Use sleep() - use proper mocking instead
- Skip tests without good reason
- Commit failing tests

---

## Quick Command Cheat Sheet

```bash
# Most common commands
./venv/bin/pytest                           # Run all tests
./venv/bin/pytest -v                        # Verbose output
./venv/bin/pytest -x                        # Stop on first failure
./venv/bin/pytest -k "audio"                # Run tests matching "audio"
./venv/bin/pytest --lf                      # Run last failed
./venv/bin/pytest --cov                     # With coverage
./venv/bin/pytest tests/path/test_file.py   # Specific file
./venv/bin/pytest -m unit                   # Only unit tests
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [TDD with Python](https://testdriven.io/blog/modern-tdd/)
- [Effective Python Testing](https://realpython.com/pytest-python-testing/)
