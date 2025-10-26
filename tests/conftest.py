"""Root test configuration for all tests."""
import os
import pytest


# CRITICAL: Force mock hardware for ALL tests to prevent real hardware activation
@pytest.fixture(scope="session", autouse=True)
def force_mock_hardware():
    """Force USE_MOCK_HARDWARE=true for all tests to prevent real hardware activation."""
    os.environ["USE_MOCK_HARDWARE"] = "true"
    yield
    # Cleanup not needed - test session ends


# CRITICAL: Stub Auth0 for ALL tests to prevent real auth calls
@pytest.fixture(scope="session", autouse=True)
def stub_auth0():
    """Stub Auth0 validation to prevent real auth service calls."""
    # This will be implemented when we add auth0 mocking
    pass
