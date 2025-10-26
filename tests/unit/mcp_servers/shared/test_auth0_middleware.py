"""
Unit tests for Auth0 middleware M2M (client_credentials) validation.

Tests JWT validation, scope checking, and client info extraction for
machine-to-machine authentication.
"""
import pytest
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
import time

from src.mcp_servers.shared.auth0_middleware import (
    check_scope,
    get_client_info,
    log_client_action,
    validate_auth0_token
)


# Test fixtures

@pytest.fixture
def mock_token_payload():
    """Mock M2M JWT payload (client_credentials grant) with operator scopes."""
    return {
        "iss": "https://test-tenant.auth0.com/",
        "sub": "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH@clients",
        "aud": "https://coffee-roasting-mcp",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "gty": "client-credentials",
        "azp": "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH",
        "scope": "read:roaster write:roaster read:detection write:detection"
    }


@pytest.fixture
def observer_token_payload():
    """Mock M2M JWT payload for observer client (read-only scopes)."""
    return {
        "iss": "https://test-tenant.auth0.com/",
        "sub": "ObserverClientId123456789@clients",
        "aud": "https://coffee-roasting-mcp",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "gty": "client-credentials",
        "azp": "ObserverClientId123456789",
        "scope": "read:roaster read:detection"
    }


# Tests for check_scope

def test_check_scope_from_scope_claim(mock_token_payload):
    """Test scope checking from 'scope' claim (space-separated string)."""
    assert check_scope(mock_token_payload, "read:roaster") == True
    assert check_scope(mock_token_payload, "write:roaster") == True
    assert check_scope(mock_token_payload, "admin:roaster") == False


def test_check_scope_empty(mock_token_payload):
    """Test scope checking with no scopes."""
    payload = mock_token_payload.copy()
    payload["scope"] = ""
    
    assert check_scope(payload, "read:roaster") == False
    assert check_scope(payload, "write:detection") == False


def test_check_scope_missing_scope(observer_token_payload):
    """Test that clients without write scopes cannot access write endpoints."""
    assert check_scope(observer_token_payload, "read:roaster") == True
    assert check_scope(observer_token_payload, "write:roaster") == False
    assert check_scope(observer_token_payload, "admin:roaster") == False


# Tests for get_client_info

def test_get_client_info_extraction(mock_token_payload):
    """Test client info extraction from M2M JWT payload."""
    client = get_client_info(mock_token_payload)
    
    assert client["client_id"] == "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH"
    assert client["grant_type"] == "client-credentials"
    assert "read:roaster" in client["scopes"]
    assert "write:roaster" in client["scopes"]


def test_get_client_info_with_multiple_scopes(mock_token_payload):
    """Test client info with multiple scopes in scope claim."""
    client = get_client_info(mock_token_payload)
    assert len(client["scopes"]) == 4
    assert "read:detection" in client["scopes"]
    assert "write:detection" in client["scopes"]


def test_get_client_info_minimal_fields():
    """Test client info extraction with minimal M2M token fields."""
    minimal_payload = {
        "azp": "minimal-client-id",
        "gty": "client-credentials",
        "scope": "read:roaster"
    }
    
    client = get_client_info(minimal_payload)
    assert client["client_id"] == "minimal-client-id"
    assert client["grant_type"] == "client-credentials"
    assert "read:roaster" in client["scopes"]


# Tests for log_client_action

def test_log_client_action_basic(mock_token_payload, caplog):
    """Test audit logging with M2M client context."""
    import logging
    caplog.set_level(logging.INFO)
    
    log_client_action(mock_token_payload, "roaster.start")
    
    assert "Client action:" in caplog.text
    assert "roaster.start" in caplog.text
    assert "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH" in caplog.text


def test_log_client_action_with_details(mock_token_payload, caplog):
    """Test audit logging with additional details."""
    import logging
    caplog.set_level(logging.INFO)
    
    log_client_action(
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
        assert result["azp"] == "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH"
        assert result["gty"] == "client-credentials"


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
    Test RBAC scenario: Observer client can read, Operator client can read and write.
    """
    # Observer can read
    assert check_scope(observer_token_payload, "read:roaster") == True
    
    # Observer cannot write
    assert check_scope(observer_token_payload, "write:roaster") == False
    
    # Operator can read
    assert check_scope(mock_token_payload, "read:roaster") == True
    
    # Operator can write
    assert check_scope(mock_token_payload, "write:roaster") == True
    
    # Get client info for audit
    observer = get_client_info(observer_token_payload)
    operator = get_client_info(mock_token_payload)
    
    assert observer["client_id"] == "ObserverClientId123456789"
    assert operator["client_id"] == "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH"
    assert "write:roaster" not in observer["scopes"]
    assert "write:roaster" in operator["scopes"]
