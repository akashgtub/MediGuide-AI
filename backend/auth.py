"""
Authentication & Role-Based Access Control (RBAC) Module for MediGuide-AI.
Enforces server-side permissions for Patients, Clinicians, and Administrators.

Safety & Security:
- Salted PBKDF2 password hashing (100,000 iterations).
- Cryptographic HMAC-SHA256 signed access tokens with expiration.
- Zero plaintext credential storage.
- Strict server-side role validation (no trusting client-reported roles).
- Granular patient data isolation.
"""

import os
import json
import time
import base64
import hmac
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from fastapi import Header, HTTPException, status, Depends
from backend.database import get_user_by_email, get_user_by_id, verify_password

# Secret key for HMAC token signing (configurable via environment variable)
SECRET_KEY = os.environ.get("MEDIGUIDE_SECRET_KEY", "mediguide-development-secret-key-change-in-production-2026")
TOKEN_EXPIRATION_SECONDS = int(os.environ.get("MEDIGUIDE_TOKEN_EXPIRY", "86400"))  # 24 hours


def _b64url_encode(data: bytes) -> str:
    """Base64 URL-safe encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Base64 URL-safe decode with padding restoration."""
    padding = "=" * (4 - (len(data) % 4)) if (len(data) % 4) != 0 else ""
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(user_id: str, email: str, role: str, name: str) -> str:
    """
    Generate a signed JWT-style bearer access token with expiration.
    Structure: header.payload.signature
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "iat": now,
        "exp": now + TOKEN_EXPIRATION_SECONDS,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate HMAC-SHA256 signature and expiration of access token.
    Returns payload dictionary if valid, None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not secrets.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))

        # Verify expiration
        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract Bearer token string from Authorization header."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization.strip()


def get_optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Retrieve currently authenticated user if token present, or None if anonymous.
    Never raises an error.
    """
    token = get_token_from_header(authorization)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user = get_user_by_id(payload.get("sub"))
    if not user or user.get("status") == "Suspended":
        return None
    return user


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Enforce active user authentication.
    Raises 401 Unauthorized if token is missing, expired, or invalid.
    """
    user = get_optional_current_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """
    Dependency factory enforcing role-based permissions (RBAC).
    Raises 403 Forbidden if the authenticated user's role is not authorized.
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, but current user has role '{user_role}'.",
            )
        return current_user
    return role_checker
