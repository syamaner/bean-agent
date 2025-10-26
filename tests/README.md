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
