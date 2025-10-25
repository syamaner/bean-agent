"""
Unit tests for Auth0 middleware user validation.

Tests JWT validation, scope checking, and user info extraction.
"""
import pytest
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
import time

from src.mcp_servers.shared.auth0_middleware import (
    check_user_scope,
    get_user_info,
    log_user_action,
    validate_auth0_token
)


# Test fixtures

@pytest.fixture
def mock_token_payload():
    """Mock JWT payload with user info and scopes."""
    return {
        "sub": "auth0|507f1f77bcf86cd799439011",
        "email": "operator@coffee.local",
        "name": "Jane Operator",
        "nickname": "jane",
        "picture": "https://example.com/avatar.jpg",
        "scope": "read:roaster write:roaster read:detection",
        "permissions": ["read:roaster", "write:roaster", "read:detection"],
        "aud": "https://coffee-roasting-api",
        "iss": "https://test-tenant.auth0.com/",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400
    }


@pytest.fixture
def observer_token_payload():
    """Mock JWT payload for observer role (read-only)."""
    return {
        "sub": "auth0|507f1f77bcf86cd799439012",
        "email": "observer@coffee.local",
        "name": "John Observer",
        "nickname": "john",
        "scope": "read:roaster read:detection",
        "permissions": ["read:roaster", "read:detection"],
        "aud": "https://coffee-roasting-api",
        "iss": "https://test-tenant.auth0.com/",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400
    }


# Tests for check_user_scope

def test_check_user_scope_from_scope_claim(mock_token_payload):
    """Test scope checking from 'scope' claim (space-separated string)."""
    assert check_user_scope(mock_token_payload, "read:roaster") == True
    assert check_user_scope(mock_token_payload, "write:roaster") == True
    assert check_user_scope(mock_token_payload, "admin:roaster") == False


def test_check_user_scope_from_permissions_claim(mock_token_payload):
    """Test scope checking from 'permissions' claim (array)."""
    # Remove scope claim to test permissions fallback
    payload = mock_token_payload.copy()
    payload["scope"] = ""
    
    assert check_user_scope(payload, "read:roaster") == True
    assert check_user_scope(payload, "write:detection") == False


def test_check_user_scope_missing_scope(observer_token_payload):
    """Test that users without write scopes cannot access write endpoints."""
    assert check_user_scope(observer_token_payload, "read:roaster") == True
    assert check_user_scope(observer_token_payload, "write:roaster") == False
    assert check_user_scope(observer_token_payload, "admin:roaster") == False


# Tests for get_user_info

def test_get_user_info_extraction(mock_token_payload):
    """Test user info extraction from JWT payload."""
    user = get_user_info(mock_token_payload)
    
    assert user["user_id"] == "auth0|507f1f77bcf86cd799439011"
    assert user["email"] == "operator@coffee.local"
    assert user["name"] == "Jane Operator"
    assert user["nickname"] == "jane"
    assert "read:roaster" in user["scopes"]
    assert "write:roaster" in user["scopes"]


def test_get_user_info_combines_scope_and_permissions(mock_token_payload):
    """Test that scopes from both 'scope' and 'permissions' are combined."""
    # Add extra permission not in scope
    payload = mock_token_payload.copy()
    payload["permissions"].append("admin:detection")
    
    user = get_user_info(payload)
    assert "admin:detection" in user["scopes"]


def test_get_user_info_missing_fields():
    """Test user info extraction when optional fields are missing."""
    minimal_payload = {
        "sub": "auth0|123",
        "scope": "read:roaster"
    }
    
    user = get_user_info(minimal_payload)
    assert user["user_id"] == "auth0|123"
    assert user["email"] is None
    assert user["name"] is None
    assert "read:roaster" in user["scopes"]


# Tests for log_user_action

def test_log_user_action_basic(mock_token_payload, caplog):
    """Test audit logging with user context."""
    import logging
    caplog.set_level(logging.INFO)
    
    log_user_action(mock_token_payload, "roaster.start")
    
    assert "User action:" in caplog.text
    assert "roaster.start" in caplog.text
    assert "operator@coffee.local" in caplog.text


def test_log_user_action_with_details(mock_token_payload, caplog):
    """Test audit logging with additional details."""
    import logging
    caplog.set_level(logging.INFO)
    
    log_user_action(
        mock_token_payload,
        "roaster.set_heat",
        {"level": 75, "previous": 50}
    )
    
    assert "roaster.set_heat" in caplog.text
    assert "level" in caplog.text


# Tests for validate_auth0_token (mocked)

@pytest.mark.asyncio
@patch.dict('os.environ', {
    'AUTH0_DOMAIN': 'test-tenant.auth0.com',
    'AUTH0_AUDIENCE': 'https://coffee-roasting-api'
}, clear=True)
@patch('src.mcp_servers.shared.auth0_middleware.get_jwks')
@patch('src.mcp_servers.shared.auth0_middleware.jwt.decode')
async def test_validate_auth0_token_success(mock_decode, mock_get_jwks, mock_token_payload):
    """Test successful token validation."""
    # Reimport to pick up mocked environment
    import src.mcp_servers.shared.auth0_middleware as auth_module
    auth_module.AUTH0_DOMAIN = 'test-tenant.auth0.com'
    auth_module.AUTH0_AUDIENCE = 'https://coffee-roasting-api'
    
    # Mock JWKS response
    mock_get_jwks.return_value = {
        "keys": [{
            "kid": "test-kid",
            "kty": "RSA",
            "use": "sig",
            "n": "test-n",
            "e": "test-e"
        }]
    }
    
    # Mock jwt.decode to return our payload
    mock_decode.return_value = mock_token_payload
    
    # Mock jwt.get_unverified_header
    with patch('src.mcp_servers.shared.auth0_middleware.jwt.get_unverified_header') as mock_header:
        mock_header.return_value = {"kid": "test-kid", "alg": "RS256"}
        
        result = await auth_module.validate_auth0_token("fake.jwt.token")
        
        assert result == mock_token_payload
        assert result["email"] == "operator@coffee.local"


@pytest.mark.asyncio
@patch.dict('os.environ', {}, clear=True)
async def test_validate_auth0_token_missing_config():
    """Test token validation fails when Auth0 config is missing."""
    import src.mcp_servers.shared.auth0_middleware as auth_module
    auth_module.AUTH0_DOMAIN = None
    auth_module.AUTH0_AUDIENCE = None
    
    with pytest.raises(ValueError, match="AUTH0_AUDIENCE"):
        await auth_module.validate_auth0_token("fake.jwt.token")


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'AUTH0_DOMAIN': 'test-tenant.auth0.com',
    'AUTH0_AUDIENCE': 'https://coffee-roasting-api'
}, clear=True)
@patch('src.mcp_servers.shared.auth0_middleware.get_jwks')
async def test_validate_auth0_token_invalid_signature(mock_get_jwks):
    """Test token validation fails with invalid signature."""
    # Reimport to pick up mocked environment
    import src.mcp_servers.shared.auth0_middleware as auth_module
    auth_module.AUTH0_DOMAIN = 'test-tenant.auth0.com'
    auth_module.AUTH0_AUDIENCE = 'https://coffee-roasting-api'
    
    mock_get_jwks.return_value = {"keys": []}
    
    with patch('src.mcp_servers.shared.auth0_middleware.jwt.get_unverified_header') as mock_header:
        mock_header.return_value = {"kid": "unknown-kid", "alg": "RS256"}
        
        with pytest.raises(JWTError, match="signing key"):
            await auth_module.validate_auth0_token("fake.jwt.token")


# Integration test for RBAC scenario

def test_rbac_scenario_observer_vs_operator(observer_token_payload, mock_token_payload):
    """
    Test RBAC scenario: Observer can read, Operator can read and write.
    """
    # Observer can read
    assert check_user_scope(observer_token_payload, "read:roaster") == True
    
    # Observer cannot write
    assert check_user_scope(observer_token_payload, "write:roaster") == False
    
    # Operator can read
    assert check_user_scope(mock_token_payload, "read:roaster") == True
    
    # Operator can write
    assert check_user_scope(mock_token_payload, "write:roaster") == True
    
    # Get user info for audit
    observer = get_user_info(observer_token_payload)
    operator = get_user_info(mock_token_payload)
    
    assert observer["email"] == "observer@coffee.local"
    assert operator["email"] == "operator@coffee.local"
    assert "write:roaster" not in observer["scopes"]
    assert "write:roaster" in operator["scopes"]
