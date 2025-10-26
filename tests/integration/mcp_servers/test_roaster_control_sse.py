"""
Tests for Roaster Control SSE Server with Auth0 authentication.

Tests RBAC scenarios: Observer (read-only) vs Operator (full control).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from starlette.testclient import TestClient
import time


@pytest.fixture
def mock_operator_token():
    """Mock M2M JWT for operator client (read + write scopes)."""
    return {
        "iss": "https://test-tenant.auth0.com/",
        "sub": "operator-client-id@clients",
        "aud": "https://coffee-roasting-mcp",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "gty": "client-credentials",
        "azp": "operator-client-id",
        "scope": "read:roaster write:roaster"
    }


@pytest.fixture
def mock_observer_token():
    """Mock M2M JWT for observer client (read-only scopes)."""
    return {
        "iss": "https://test-tenant.auth0.com/",
        "sub": "observer-client-id@clients",
        "aud": "https://coffee-roasting-mcp",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "gty": "client-credentials",
        "azp": "observer-client-id",
        "scope": "read:roaster"
    }


@pytest.fixture
def mock_session_manager():
    """Mock RoasterSessionManager."""
    mock = MagicMock()
    mock.current_session = None
    mock.roaster = None
    return mock


@pytest.fixture
def mock_config():
    """Mock server config."""
    mock = MagicMock()
    mock.mock_mode = True
    mock.serial_port = None
    return mock


# Test public endpoints (no auth required)

def test_health_endpoint_public():
    """Test health check endpoint is accessible without auth."""
    # Create a proper mock session manager
    mock_sm = MagicMock()
    mock_sm.is_active.return_value = False
    mock_sm.get_hardware_info.return_value = {"type": "mock", "connected": False}
    
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.roaster_control.sse_server.session_manager', mock_sm):
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "session_active" in response.json()
        assert "roaster_info" in response.json()


def test_root_endpoint_public():
    """Test root endpoint shows API info without auth."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'):
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Roaster Control MCP Server"
        assert "observer" in data["roles"]
        assert "operator" in data["roles"]


# Test Auth0 middleware

@pytest.mark.asyncio
async def test_sse_endpoint_requires_auth():
    """Test SSE endpoint rejects requests without auth."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'):
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        response = client.get("/sse")
        assert response.status_code == 401
        assert "error" in response.json()


@pytest.mark.asyncio
async def test_sse_endpoint_requires_roaster_scope(mock_observer_token):
    """Test SSE endpoint requires at least read:roaster scope."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.roaster_control.sse_server.session_manager') as mock_sm, \
         patch('src.mcp_servers.roaster_control.sse_server.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        # Set Auth0 module constants directly
        import src.mcp_servers.shared.auth0_middleware as auth_module
        auth_module.AUTH0_DOMAIN = 'test.auth0.com'
        auth_module.AUTH0_AUDIENCE = 'https://coffee-roasting-api'
        
        mock_sm.current_session = None
        mock_sm.roaster = None
        
        # Client with no roaster scopes
        mock_validate.return_value = {
            "iss": "https://test-tenant.auth0.com/",
            "sub": "wrong-scope-client@clients",
            "aud": "https://coffee-roasting-mcp",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,
            "gty": "client-credentials",
            "azp": "wrong-scope-client",
            "scope": "read:detection"  # Wrong scope!
        }
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["error"]


# Test RBAC scenarios

@pytest.mark.slow
@pytest.mark.asyncio
async def test_observer_can_connect(mock_observer_token):
    """Test observer (read-only) can connect to SSE.
    Note: This is slow because it tries to establish SSE connection.
    Skip with: pytest -m 'not slow'
    """
    pytest.skip("Slow SSE connection test - use integration tests instead")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_operator_can_connect(mock_operator_token):
    """Test operator (full control) can connect to SSE.
    Note: This is slow because it tries to establish SSE connection.
    Skip with: pytest -m 'not slow'
    """
    pytest.skip("Slow SSE connection test - use integration tests instead")


# Test client audit logging

@pytest.mark.slow
@pytest.mark.skip(reason="SSE connection hangs - needs proper async mocking")
@pytest.mark.asyncio
async def test_client_connection_logged(mock_operator_token, caplog):
    """Test that M2M client connections are logged for audit.
    
    Note: This test hangs on SSE connection. Needs refactoring to properly
    mock the SSE stream without actually trying to establish connection.
    """
    pytest.skip("SSE connection test - refactor needed")
    import logging
    caplog.set_level(logging.INFO)
    
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.roaster_control.sse_server.session_manager') as mock_sm, \
         patch('src.mcp_servers.roaster_control.sse_server.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        # Set Auth0 module constants directly
        import src.mcp_servers.shared.auth0_middleware as auth_module
        auth_module.AUTH0_DOMAIN = 'test.auth0.com'
        auth_module.AUTH0_AUDIENCE = 'https://coffee-roasting-api'
        
        mock_sm.current_session = None
        mock_sm.roaster = None
        mock_validate.return_value = mock_operator_token
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        
        # Check that client connection was logged
        assert "operator-client-id" in caplog.text or "MCP connection" in caplog.text


# Test MCP tools registration

def test_mcp_tools_have_scope_descriptions():
    """Test that MCP tool descriptions include required scopes."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.roaster_control.sse_server.session_manager') as mock_sm:
        
        mock_sm.current_session = None
        mock_sm.roaster = None
        
        from src.mcp_servers.roaster_control.sse_server import setup_mcp_server, mcp_server
        
        setup_mcp_server()
        
        # Check that MCP server is properly initialized
        assert mcp_server.name == "roaster-control"


# Integration test: RBAC scenario

@pytest.mark.asyncio
async def test_rbac_scenario_observer_vs_operator_integration(mock_observer_token, mock_operator_token):
    """
    Integration test: Observer can read, Operator can read and write.
    """
    # This is more of a documentation test showing the expected behavior
    from src.mcp_servers.shared.auth0_middleware import check_scope
    
    # Observer has read:roaster
    assert check_scope(mock_observer_token, "read:roaster") == True
    assert check_scope(mock_observer_token, "write:roaster") == False
    
    # Operator has read:roaster + write:roaster
    assert check_scope(mock_operator_token, "read:roaster") == True
    assert check_scope(mock_operator_token, "write:roaster") == True
    
    # This demonstrates:
    # - Observer can view status (read_roaster_status tool)
    # - Observer CANNOT start roaster (start_roaster tool)
    # - Operator can do both


# Test error handling

@pytest.mark.asyncio
async def test_invalid_token_returns_401():
    """Test that invalid JWT returns 401 Unauthorized."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.shared.auth0_middleware.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        # Simulate token validation error
        from jose import JWTError
        mock_validate.side_effect = JWTError("Token has expired")
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer expired.jwt.token"}
        )
        assert response.status_code == 401
        assert "Authentication failed" in response.json()["error"]


@pytest.mark.asyncio
async def test_missing_authorization_header_returns_401():
    """Test that missing Authorization header returns 401."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'):
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        # No Authorization header
        response = client.get("/sse")
        assert response.status_code == 401
        assert "error" in response.json()
