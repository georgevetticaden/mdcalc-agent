"""
OAuth token validation for MDCalc MCP Server.
Validates JWT tokens issued by Auth0 using JWKS.
"""

import httpx
from jose import jwt, JWTError
from typing import Dict
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from .config import settings


# HTTP Bearer security scheme
security = HTTPBearer()


@lru_cache(maxsize=1)
def get_jwks() -> Dict:
    """
    Fetch JSON Web Key Set from Auth0.
    Cached to avoid repeated requests.
    """
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"

    try:
        response = httpx.get(jwks_url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch JWKS: {str(e)}"
        )


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    Verify JWT token from Authorization header.

    Validates:
    - Token signature (using JWKS from Auth0)
    - Token expiration
    - Issuer matches Auth0
    - Audience matches API identifier

    Args:
        credentials: HTTP Authorization credentials from request

    Returns:
        Decoded token payload with scopes

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Get JWKS from Auth0
        jwks = get_jwks()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)

        # Find matching key in JWKS
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

        if rsa_key is None:
            raise HTTPException(
                status_code=401,
                detail="Unable to find appropriate key in JWKS"
            )

        # Verify and decode token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_API_AUDIENCE,
            issuer=settings.AUTH0_ISSUER
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token validation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}"
        )


def get_token_scopes(token_payload: Dict) -> list:
    """
    Extract scopes from decoded token payload.

    Args:
        token_payload: Decoded JWT token

    Returns:
        List of scope strings (e.g., ["mdcalc:read", "mdcalc:calculate"])
    """
    # Auth0 stores scopes as space-separated string
    scopes_string = token_payload.get("scope", "")
    return scopes_string.split() if scopes_string else []


def require_scope(required_scope: str, token_scopes: list) -> None:
    """
    Verify that token has required scope.

    Args:
        required_scope: Scope needed for the operation
        token_scopes: Scopes present in the token

    Raises:
        HTTPException: If required scope is missing
    """
    if required_scope not in token_scopes:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required scope: {required_scope}"
        )
