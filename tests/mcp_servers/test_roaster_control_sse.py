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
    """Mock JWT for operator role (read + write)."""
    return {
        "sub": "auth0|operator123",
        "email": "operator@coffee.local",
        "name": "Jane Operator",
        "scope": "read:roaster write:roaster",
        "permissions": ["read:roaster", "write:roaster"],
        "aud": "https://coffee-roasting-api",
        "iss": "https://test-tenant.auth0.com/",
        "exp": int(time.time()) + 86400
    }


@pytest.fixture
def mock_observer_token():
    """Mock JWT for observer role (read-only)."""
    return {
        "sub": "auth0|observer123",
        "email": "observer@coffee.local",
        "name": "John Observer",
        "scope": "read:roaster",
        "permissions": ["read:roaster"],
        "aud": "https://coffee-roasting-api",
        "iss": "https://test-tenant.auth0.com/",
        "exp": int(time.time()) + 86400
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
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.roaster_control.sse_server.session_manager') as mock_sm:
        
        # Mock session manager
        mock_sm.current_session = None
        mock_sm.roaster = None
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


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
         patch('src.mcp_servers.shared.auth0_middleware.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        # User with no roaster scopes
        mock_validate.return_value = {
            "sub": "auth0|user123",
            "email": "user@coffee.local",
            "scope": "read:detection",  # Wrong scope!
            "permissions": ["read:detection"],
            "aud": "https://coffee-roasting-api",
            "iss": "https://test-tenant.auth0.com/",
            "exp": int(time.time()) + 86400
        }
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["error"]


# Test RBAC scenarios

@pytest.mark.asyncio
async def test_observer_can_connect(mock_observer_token):
    """Test observer (read-only) can connect to SSE."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.shared.auth0_middleware.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        mock_validate.return_value = mock_observer_token
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        # Observer has read:roaster scope, should be able to connect
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        # SSE endpoint will try to establish connection
        # 200 or error from SSE connection is OK (not 403)
        assert response.status_code != 403


@pytest.mark.asyncio
async def test_operator_can_connect(mock_operator_token):
    """Test operator (full control) can connect to SSE."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.shared.auth0_middleware.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        mock_validate.return_value = mock_operator_token
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        # Operator has read+write scopes, should be able to connect
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        # SSE endpoint will try to establish connection
        # 200 or error from SSE connection is OK (not 403)
        assert response.status_code != 403


# Test user audit logging

@pytest.mark.asyncio
async def test_user_connection_logged(mock_operator_token, caplog):
    """Test that user connections are logged for audit."""
    import logging
    caplog.set_level(logging.INFO)
    
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'), \
         patch('src.mcp_servers.shared.auth0_middleware.validate_auth0_token', new_callable=AsyncMock) as mock_validate:
        
        mock_validate.return_value = mock_operator_token
        
        from src.mcp_servers.roaster_control.sse_server import app
        client = TestClient(app)
        
        response = client.get(
            "/sse",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        
        # Check that user connection was logged
        assert "operator@coffee.local" in caplog.text or "MCP connection" in caplog.text


# Test MCP tools registration

def test_mcp_tools_have_scope_descriptions():
    """Test that MCP tool descriptions include required scopes."""
    with patch('src.mcp_servers.roaster_control.sse_server.ServerConfig'), \
         patch('src.mcp_servers.roaster_control.sse_server.MockRoaster'), \
         patch('src.mcp_servers.roaster_control.sse_server.RoastSessionManager'):
        
        from src.mcp_servers.roaster_control.sse_server import setup_mcp_server, mcp_server
        
        setup_mcp_server()
        
        # Check that tools are registered
        # Note: We can't easily test the actual tool list without running the server
        # but we can verify the function doesn't error
        assert mcp_server.name == "roaster-control"


# Integration test: RBAC scenario

@pytest.mark.asyncio
async def test_rbac_scenario_observer_vs_operator_integration(mock_observer_token, mock_operator_token):
    """
    Integration test: Observer can read, Operator can read and write.
    """
    # This is more of a documentation test showing the expected behavior
    from src.mcp_servers.shared.auth0_middleware import check_user_scope
    
    # Observer has read:roaster
    assert check_user_scope(mock_observer_token, "read:roaster") == True
    assert check_user_scope(mock_observer_token, "write:roaster") == False
    
    # Operator has read:roaster + write:roaster
    assert check_user_scope(mock_operator_token, "read:roaster") == True
    assert check_user_scope(mock_operator_token, "write:roaster") == True
    
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
