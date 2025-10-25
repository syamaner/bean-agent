"""
Auth0 JWT Validation Middleware

User-based authentication with role-based access control (RBAC).
Validates user JWT tokens and extracts user information for audit logging.

Usage:
    from src.mcp_servers.shared.auth0_middleware import (
        validate_auth0_token,
        check_user_scope,
        get_user_info
    )
"""
import os
import time
import logging
from typing import Optional
from functools import lru_cache

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
    Validate Auth0 user JWT token and return payload.
    
    Validates:
    - JWT signature using Auth0 public keys
    - Token not expired
    - Audience matches API identifier
    - Issuer matches Auth0 domain
    
    Args:
        token: JWT access token string
    
    Returns:
        dict: Token payload containing user info and permissions
            {
                "sub": "auth0|507f...",  # User ID
                "email": "user@example.com",
                "name": "John Doe",
                "scope": "read:roaster write:roaster",
                "permissions": ["read:roaster", "write:roaster"],
                "aud": "https://coffee-roasting-api",
                "iss": "https://your-tenant.auth0.com/",
                "exp": 1730086400,
                ...
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
        
        logger.debug(f"Token validated for user: {payload.get('email', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise JWTError("Token has expired")
    except jwt.JWTClaimsError as e:
        raise JWTError(f"Invalid token claims: {e}")
    except Exception as e:
        raise JWTError(f"Token validation failed: {e}")


def check_user_scope(payload: dict, required_scope: str) -> bool:
    """
    Check if user token has required scope/permission.
    
    Checks both 'scope' (space-separated string) and 'permissions' (array)
    claims to support different Auth0 configurations.
    
    Args:
        payload: Decoded JWT payload
        required_scope: Scope to check (e.g., "write:roaster")
    
    Returns:
        bool: True if user has the scope, False otherwise
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> if check_user_scope(token_payload, "write:roaster"):
        ...     # User can control roaster
        ...     start_roaster()
    """
    # Check 'scope' claim (space-separated string)
    scopes = payload.get("scope", "").split()
    if required_scope in scopes:
        return True
    
    # Check 'permissions' claim (array) - used when RBAC is enabled
    permissions = payload.get("permissions", [])
    if required_scope in permissions:
        return True
    
    return False


def get_user_info(payload: dict) -> dict:
    """
    Extract user information from JWT payload for audit logging.
    
    Args:
        payload: Decoded JWT payload
    
    Returns:
        dict: User information
            {
                "user_id": "auth0|507f...",
                "email": "user@example.com",
                "name": "John Doe",
                "nickname": "john",
                "picture": "https://...",
                "scopes": ["read:roaster", "write:roaster"]
            }
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> user = get_user_info(token_payload)
        >>> logger.info(f"Action performed by {user['email']}")
    """
    # Extract scopes
    scopes = payload.get("scope", "").split()
    permissions = payload.get("permissions", [])
    all_scopes = list(set(scopes + permissions))
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "nickname": payload.get("nickname"),
        "picture": payload.get("picture"),
        "scopes": all_scopes
    }


def log_user_action(payload: dict, action: str, details: Optional[dict] = None):
    """
    Log user action for audit trail.
    
    Args:
        payload: Decoded JWT payload
        action: Action performed (e.g., "roaster.start")
        details: Optional additional details
    
    Example:
        >>> token_payload = await validate_auth0_token(token)
        >>> log_user_action(
        ...     token_payload,
        ...     "roaster.set_heat",
        ...     {"level": 75}
        ... )
    """
    user = get_user_info(payload)
    
    log_data = {
        "action": action,
        "user_id": user["user_id"],
        "user_email": user["email"],
        "user_name": user["name"],
    }
    
    if details:
        log_data["details"] = details
    
    logger.info(f"User action: {log_data}")


# FastAPI dependency helpers

def requires_scope(required_scope: str):
    """
    FastAPI dependency decorator to require specific scope.
    
    Usage:
        @app.post("/api/roaster/start")
        @requires_scope("write:roaster")
        async def start_roaster(token_payload: dict = Depends(validate_auth0_token)):
            # Token validated and scope checked
            user = get_user_info(token_payload)
            logger.info(f"Roaster started by {user['email']}")
            ...
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get token payload from request state
            # (assumes middleware has already validated and stored it)
            from fastapi import Request
            
            # Find Request in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            if not request or not hasattr(request.state, "auth"):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            token_payload = request.state.auth
            
            # Check scope
            if not check_user_scope(token_payload, required_scope):
                from fastapi import HTTPException
                user = get_user_info(token_payload)
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Insufficient permissions",
                        "required_scope": required_scope,
                        "user_scopes": user["scopes"],
                        "user_email": user["email"]
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
