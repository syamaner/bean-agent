#!/bin/bash
# Test Reorganization Script
# Organizes tests to match src/ structure and separate unit/integration/manual tests

set -e

echo "🧪 Coffee Roasting Project - Test Reorganization"
echo "================================================"
echo ""

# Create new test structure
echo "📁 Creating organized test structure..."

# Unit tests (fast, no external dependencies)
mkdir -p tests/unit/mcp_servers/roaster_control
mkdir -p tests/unit/mcp_servers/first_crack_detection
mkdir -p tests/unit/mcp_servers/shared
mkdir -p tests/unit/inference
mkdir -p tests/unit/orchestration

# Integration tests (require multiple components, may use mock hardware)
mkdir -p tests/integration/mcp_servers
mkdir -p tests/integration/orchestration

# Manual tests (require human interaction or real hardware)
mkdir -p tests/manual/hardware
mkdir -p tests/manual/mcp_servers

# E2E tests (full system tests)
mkdir -p tests/e2e

# Validation tests (environment/setup validation)
mkdir -p tests/validation

echo "✅ Directories created"
echo ""

# Move unit tests
echo "📦 Organizing unit tests..."

# MCP Servers - Roaster Control
if [ -d "tests/mcp_servers/roaster_control/unit" ]; then
    cp -r tests/mcp_servers/roaster_control/unit/* tests/unit/mcp_servers/roaster_control/ 2>/dev/null || true
fi

# MCP Servers - First Crack Detection  
if [ -d "tests/mcp_servers/first_crack_detection/unit" ]; then
    cp -r tests/mcp_servers/first_crack_detection/unit/* tests/unit/mcp_servers/first_crack_detection/ 2>/dev/null || true
fi

# Shared middleware
if [ -f "tests/mcp_servers/test_auth0_middleware.py" ]; then
    cp tests/mcp_servers/test_auth0_middleware.py tests/unit/mcp_servers/shared/ 2>/dev/null || true
fi

echo "✅ Unit tests organized"
echo ""

# Move integration tests
echo "🔗 Organizing integration tests..."

if [ -d "tests/mcp_servers/roaster_control/integration" ]; then
    cp -r tests/mcp_servers/roaster_control/integration/* tests/integration/mcp_servers/ 2>/dev/null || true
fi

if [ -d "tests/mcp_servers/first_crack_detection/integration" ]; then
    cp -r tests/mcp_servers/first_crack_detection/integration/* tests/integration/mcp_servers/ 2>/dev/null || true
fi

if [ -f "tests/mcp_servers/test_roaster_control_sse.py" ]; then
    cp tests/mcp_servers/test_roaster_control_sse.py tests/integration/mcp_servers/ 2>/dev/null || true
fi

echo "✅ Integration tests organized"
echo ""

# Move manual tests
echo "✋ Organizing manual tests..."

# Hardware tests from scripts/testing
cp scripts/testing/test_hottop_*.py tests/manual/hardware/ 2>/dev/null || true
cp scripts/testing/test_pyhottop_raw.py tests/manual/hardware/ 2>/dev/null || true

# Manual MCP tests
if [ -d "tests/mcp_servers/first_crack_detection" ]; then
    cp tests/mcp_servers/first_crack_detection/manual_*.py tests/manual/mcp_servers/ 2>/dev/null || true
    cp tests/mcp_servers/first_crack_detection/quick_test.py tests/manual/mcp_servers/ 2>/dev/null || true
fi

cp scripts/testing/test_mcp_roaster.py tests/manual/mcp_servers/ 2>/dev/null || true

echo "✅ Manual tests organized"
echo ""

# Move E2E tests
echo "🌐 Organizing E2E tests..."

# Orchestration tests
if [ -f "tests/phase3/test_autonomous_agent.py" ]; then
    cp tests/phase3/test_autonomous_agent.py tests/e2e/test_autonomous_agent.py 2>/dev/null || true
fi

cp scripts/testing/test_demo_mode_aspire.sh tests/e2e/ 2>/dev/null || true
cp scripts/testing/test_roaster_server.sh tests/e2e/ 2>/dev/null || true

echo "✅ E2E tests organized"
echo ""

# Move validation tests
echo "✔️  Organizing validation tests..."

if [ -d "tests/validation" ]; then
    # Already in correct place, just verify
    echo "   Validation tests already in place"
fi

# Move inference tests
if [ -d "tests/inference" ]; then
    cp -r tests/inference/* tests/unit/inference/ 2>/dev/null || true
fi

echo "✅ Validation tests organized"
echo ""

# Create __init__.py files
echo "📝 Creating __init__.py files..."
find tests/unit tests/integration tests/manual tests/e2e tests/validation -type d -exec touch {}/__init__.py \; 2>/dev/null || true
echo "✅ __init__.py files created"
echo ""

# Create test README
echo "📄 Creating test documentation..."
cat > tests/README.md << 'EOF'
# Coffee Roasting Tests

Organized test suite for the coffee roasting project.

## Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   ├── mcp_servers/
│   │   ├── roaster_control/       # Roaster control unit tests
│   │   ├── first_crack_detection/ # FC detection unit tests
│   │   └── shared/                # Shared middleware tests
│   ├── inference/                 # Inference API tests
│   └── orchestration/             # Orchestration logic tests
│
├── integration/                    # Integration tests (multiple components)
│   ├── mcp_servers/               # MCP server integration tests
│   └── orchestration/             # Orchestration integration tests
│
├── manual/                         # Manual tests (human interaction required)
│   ├── hardware/                  # Hardware tests (Hottop roaster)
│   └── mcp_servers/               # Manual MCP client tests
│
├── e2e/                           # End-to-end tests (full system)
│   ├── test_autonomous_agent.py   # Agent E2E tests
│   ├── test_demo_mode_aspire.sh   # Aspire demo mode test
│   └── test_roaster_server.sh     # Server E2E test
│
└── validation/                     # Environment validation
    ├── test_mps.py                # MPS availability
    └── test_audio.py              # Audio device validation
```

## Running Tests

### Unit Tests (Fast)
```bash
# All unit tests
pytest tests/unit/

# Specific component
pytest tests/unit/mcp_servers/roaster_control/
pytest tests/unit/inference/
```

### Integration Tests
```bash
# All integration tests
pytest tests/integration/

# MCP servers
pytest tests/integration/mcp_servers/
```

### Manual Tests
```bash
# Hardware tests (requires Hottop connected)
cd tests/manual/hardware
./venv/bin/python test_hottop_interactive.py

# MCP client tests
cd tests/manual/mcp_servers
./venv/bin/python manual_test_client.py
```

### E2E Tests
```bash
# Aspire orchestration test
cd tests/e2e
./test_demo_mode_aspire.sh

# Autonomous agent test
pytest tests/e2e/test_autonomous_agent.py
```

### Validation Tests
```bash
# Validate environment
pytest tests/validation/
```

## Test Categories

### Unit Tests
- ✅ Fast (< 1 second each)
- ✅ No external dependencies
- ✅ Mock all I/O
- ✅ Test single functions/classes

### Integration Tests
- ⚙️ Test multiple components together
- ⚙️ May use mock hardware
- ⚙️ Test API contracts
- ⚙️ Database/file I/O allowed

### Manual Tests
- 👤 Require human interaction
- 🔌 Require real hardware
- 🎧 Require audio devices
- 📝 Interactive prompts

### E2E Tests
- 🌐 Full system tests
- 🚀 Test via Aspire orchestration
- 🤖 Test autonomous agent
- 📊 Verify complete workflows

### Validation Tests
- ✔️ Environment setup
- ✔️ Hardware availability
- ✔️ Library compatibility

## CI/CD

### Fast Tests (Unit + Validation)
```bash
pytest tests/unit tests/validation -v
```

### Full Suite (Unit + Integration)
```bash
pytest tests/unit tests/integration -v
```

### Manual Tests
Run manually before releases with real hardware.

## Coverage

Generate coverage report:
```bash
pytest tests/unit tests/integration --cov=src --cov-report=html
```

## Related

- Source code: `src/`
- Documentation: `docs/`
- Scripts: `scripts/`
EOF

echo "✅ Test documentation created"
echo ""

# Create pytest.ini
echo "⚙️  Creating pytest configuration..."
cat > pytest.ini << 'EOF'
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests

# Markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (multiple components)
    manual: Manual tests (require human interaction)
    e2e: End-to-end tests (full system)
    slow: Slow tests (> 5 seconds)
    hardware: Requires real hardware
    audio: Requires audio devices

# Output
console_output_style = progress
addopts = 
    -ra
    --strict-markers
    --tb=short
    --disable-warnings

# Coverage
[coverage:run]
source = src
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
EOF

echo "✅ pytest configuration created"
echo ""

echo "✨ Test reorganization complete!"
echo ""
echo "New structure:"
echo "  tests/unit/           - Fast unit tests"
echo "  tests/integration/    - Integration tests"
echo "  tests/manual/         - Manual/hardware tests"
echo "  tests/e2e/            - End-to-end tests"
echo "  tests/validation/     - Environment validation"
echo ""
echo "Run tests:"
echo "  pytest tests/unit/                    # Fast unit tests"
echo "  pytest tests/integration/             # Integration tests"
echo "  pytest tests/                         # All automated tests"
echo "  pytest -m unit                        # Only unit tests"
echo "  pytest -m \"not manual\"                # Skip manual tests"
echo ""
echo "Next: Review and delete old test directories"
echo "  rm -rf tests/mcp_servers tests/phase3 tests/inference"
