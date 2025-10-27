"""
Auth0 JWT Validation Middleware

Machine-to-Machine (M2M) authentication with role-based access control (RBAC).
Validates M2M JWT tokens from client_credentials grant and extracts client
information for audit logging.

Usage:
    from src.mcp_servers.shared.auth0_middleware import (
        validate_auth0_token,
        check_scope,
        get_client_info
    )
"""
import os
import time
import logging
from typing import Optional

import requests
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

# JWKS cache
_jwks_cache = None
_jwks_cache_time = None
JWKS_CACHE_DURATION = 3600  # 1 hour


def get_jwks():
    """
    Fetch Auth0 JSON Web Key Set (JWKS) for JWT validation.
    
    Caches keys for 1 hour to minimize Auth0 API calls.
    
    Returns:
        dict: JWKS containing public keys
    """
    global _jwks_cache, _jwks_cache_time
    
    now = time.time()
    if _jwks_cache and (_jwks_cache_time + JWKS_CACHE_DURATION > now):
        return _jwks_cache
    
    if not AUTH0_DOMAIN:
        raise ValueError("AUTH0_DOMAIN environment variable not set")
    
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        _jwks_cache = response.json()
        _jwks_cache_time = now
        
        logger.info("JWKS keys refreshed from Auth0")
        return _jwks_cache
        
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        if _jwks_cache:
            logger.warning("Using stale JWKS cache")
            return _jwks_cache
        raise


async def validate_auth0_token(token: str) -> dict:
    """
    Validate Auth0 M2M JWT token (client_credentials grant) and return payload.
    
    Validates:
    - JWT signature using Auth0 public keys
    - Token not expired
    - Audience matches API identifier
    - Issuer matches Auth0 domain
    
    Args:
        token: JWT access token string
    
    Returns:
        dict: Token payload containing client info and scopes
            {
                "iss": "https://your-tenant.auth0.com/",
                "sub": "client-id@clients",
                "aud": "https://coffee-roasting-mcp",
                "iat": 1730086400,
                "exp": 1730172800,
                "gty": "client-credentials",
                "azp": "client-id",
                "scope": "read:roaster write:roaster"
            }
    
    Raises:
        JWTError: If token is invalid, expired, or signature doesn't verify
        ValueError: If configuration is missing
    """
    if not AUTH0_AUDIENCE:
        raise ValueError("AUTH0_AUDIENCE environment variable not set")
    
    if not AUTH0_DOMAIN:
        raise ValueError("AUTH0_DOMAIN environment variable not set")
    
    # Get JWKS
    jwks = get_jwks()
    
    # Get the key ID from token header
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise JWTError(f"Invalid token header: {e}")
    
    # Find matching key
    rsa_key = None
    for key in jwks.get("keys", []):
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise JWTError("Unable to find appropriate signing key")
    
    # Verify and decode token
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        client_id = payload.get('azp', payload.get('sub', 'unknown'))
        logger.debug(f"Token validated for client: {client_id}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise JWTError("Token has expired")
    except jwt.JWTClaimsError as e:
        raise JWTError(f"Invalid token claims: {e}")
    except Exception as e:
        raise JWTError(f"Token validation failed: {e}")


def check_scope(payload: dict, required_scope: str) -> bool:
    """
    Check if M2M client token has required scope.
    
    Checks 'scope' claim (space-separated string) from client_credentials grant.
    
    Args:
        payload: Decoded M2M JWT payload
        required_scope: Scope to check (e.g., "write:roaster")
    
    Returns:
        bool: True if client has the scope, False otherwise
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> if check_scope(token_payload, "write:roaster"):
        ...     # Client can control roaster
        ...     start_roaster()
    """
    scopes = payload.get("scope", "").split()
    return required_scope in scopes


def get_client_info(payload: dict) -> dict:
    """
    Extract client information from M2M JWT payload for audit logging.
    
    Args:
        payload: Decoded M2M JWT payload
    
    Returns:
        dict: Client information
            {
                "client_id": "client-id-string",
                "grant_type": "client-credentials",
                "scopes": ["read:roaster", "write:roaster"]
            }
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> client = get_client_info(token_payload)
        >>> logger.info(f"Action performed by client {client['client_id']}")
    """
    scopes = payload.get("scope", "").split()
    
    return {
        "client_id": payload.get("azp", payload.get("sub", "unknown")),
        "grant_type": payload.get("gty", "unknown"),
        "scopes": [s for s in scopes if s]  # Filter empty strings
    }


def log_client_action(payload: dict, action: str, details: Optional[dict] = None):
    """
    Log M2M client action for audit trail.
    
    Args:
        payload: Decoded M2M JWT payload
        action: Action performed (e.g., "roaster.start")
        details: Optional additional details
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> log_client_action(
        ...     token_payload,
        ...     "roaster.set_heat",
        ...     {"level": 75}
        ... )
    """
    client = get_client_info(payload)
    
    log_data = {
        "action": action,
        "client_id": client["client_id"],
        "grant_type": client["grant_type"],
    }
    
    if details:
        log_data["details"] = details
    
    logger.info(f"Client action: {log_data}")


# Backward compatibility aliases
check_user_scope = check_scope
get_user_info = get_client_info
log_user_action = log_client_action
