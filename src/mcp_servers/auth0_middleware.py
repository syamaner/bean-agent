"""Auth0 JWT validation middleware for MCP HTTP servers.

This module provides JWT validation and scope-based authorization
for protecting MCP HTTP endpoints with Auth0.

Usage:
    from src.mcp_servers.auth0_middleware import requires_scope

    @app.post("/api/roaster/start")
    @requires_scope("write:roaster")
    async def start_roaster():
        # Endpoint is now protected
        ...
"""
import os
import time
from functools import wraps
from typing import Optional

import requests
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError


# ============================================
# Configuration
# ============================================

def get_auth0_config():
    """Get Auth0 configuration from environment variables.
    
    Returns:
        tuple: (domain, audience, algorithms)
    
    Raises:
        ValueError: If required environment variables are not set
    """
    domain = os.environ.get("AUTH0_DOMAIN")
    audience = os.environ.get("AUTH0_AUDIENCE")
    
    if not domain or not audience:
        raise ValueError(
            "Missing Auth0 configuration. "
            "Set AUTH0_DOMAIN and AUTH0_AUDIENCE environment variables."
        )
    
    return domain, audience, ["RS256"]


# ============================================
# JWKS Caching
# ============================================

_jwks_cache: Optional[dict] = None
_jwks_cache_time: Optional[float] = None
JWKS_CACHE_DURATION = 3600  # 1 hour


def get_jwks(domain: str) -> dict:
    """Fetch Auth0 public keys for JWT verification.
    
    Uses 1-hour caching to reduce API calls.
    
    Args:
        domain: Auth0 tenant domain
    
    Returns:
        JWKS response from Auth0
    
    Raises:
        HTTPException: If JWKS endpoint is unreachable
    """
    global _jwks_cache, _jwks_cache_time
    
    now = time.time()
    if _jwks_cache and _jwks_cache_time and (_jwks_cache_time + JWKS_CACHE_DURATION > now):
        return _jwks_cache
    
    url = f"https://{domain}/.well-known/jwks.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch JWKS from Auth0: {str(e)}"
        )
    
    _jwks_cache = response.json()
    _jwks_cache_time = now
    return _jwks_cache


# ============================================
# Token Validation
# ============================================

def get_token_from_header(request: Request) -> str:
    """Extract Bearer token from Authorization header.
    
    Args:
        request: FastAPI request object
    
    Returns:
        JWT token string
    
    Raises:
        HTTPException: If token is missing or malformed
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]


def verify_token(token: str, domain: str, audience: str, algorithms: list[str]) -> dict:
    """Verify JWT token and return claims.
    
    Args:
        token: JWT token string
        domain: Auth0 tenant domain
        audience: Expected API audience
        algorithms: Allowed signing algorithms
    
    Returns:
        Token payload (claims)
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        jwks = get_jwks(domain)
    except HTTPException:
        raise
    
    # Get the key ID from token header
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find matching key
    rsa_key = None
    for key in jwks["keys"]:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate signing key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify and decode token
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=algorithms,
            audience=audience,
            issuer=f"https://{domain}/"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


# ============================================
# Scope Authorization
# ============================================

def requires_scope(required_scope: str):
    """Decorator to enforce scope-based authorization on FastAPI endpoints.
    
    Usage:
        @app.post("/api/roaster/start")
        @requires_scope("write:roaster")
        async def start_roaster():
            ...
    
    Args:
        required_scope: Scope that must be present in token (e.g., "write:roaster")
    
    Returns:
        Decorated function that validates JWT and checks scope
    
    Raises:
        HTTPException: 401 if token invalid, 403 if scope missing
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get configuration
            domain, audience, algorithms = get_auth0_config()
            
            # Extract and verify token
            token = get_token_from_header(request)
            payload = verify_token(token, domain, audience, algorithms)
            
            # Check scope
            token_scopes = payload.get("scope", "").split()
            if required_scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required scope: {required_scope}",
                )
            
            # Store user info in request state for downstream use
            request.state.user_id = payload.get("sub")
            request.state.scopes = token_scopes
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ============================================
# Optional: Helper for checking multiple scopes
# ============================================

def check_any_scope(payload: dict, required_scopes: list[str]) -> bool:
    """Check if token has at least one of the required scopes.
    
    Args:
        payload: JWT payload
        required_scopes: List of acceptable scopes
    
    Returns:
        True if any scope matches
    """
    token_scopes = payload.get("scope", "").split()
    return any(scope in token_scopes for scope in required_scopes)
