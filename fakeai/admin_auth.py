#!/usr/bin/env python3
"""
Admin Authentication Module for FakeAI

This module provides simple session-based authentication for admin routes.
This is a demo/testing tool - NOT for production use.

Features:
- Fake login (any username/password works for demo purposes)
- JWT token generation and validation
- Session management
- Middleware for protecting admin routes
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Annotated, Optional

import jwt
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Simple in-memory session store
# In production, use Redis or a proper database
_sessions: dict[str, "AdminSession"] = {}

# JWT Secret - load from environment variable
JWT_SECRET = os.environ.get("FAKEAI_JWT_SECRET")
if not JWT_SECRET:
    # Generate a random secret for this session if not provided
    # WARNING: This means tokens won't survive server restarts
    JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning(
        "FAKEAI_JWT_SECRET not set in environment. Using random session secret. "
        "Set FAKEAI_JWT_SECRET environment variable for persistent tokens.")

JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60


class AdminSession(BaseModel):
    """Admin session data"""
    username: str
    token: str
    created_at: float
    expires_at: float
    last_activity: float


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    success: bool
    token: str
    username: str
    expires_in: int


class LogoutResponse(BaseModel):
    """Logout response model"""
    success: bool
    message: str


class VerifyResponse(BaseModel):
    """Verify session response model"""
    valid: bool
    username: Optional[str] = None
    expires_in: Optional[int] = None


def generate_token(username: str) -> str:
    """
    Generate a JWT token for the user using PyJWT library.

    Args:
        username: The username to encode in the token

    Returns:
        A properly signed JWT token
    """
    now = datetime.utcnow()
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and return the username.

    Uses PyJWT for proper cryptographic verification.
    Returns None if token is invalid or expired.

    Args:
        token: The JWT token to verify

    Returns:
        The username if token is valid, None otherwise
    """
    try:
        # Decode and verify the JWT token
        # PyJWT automatically verifies signature, expiration, and other claims
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        username = payload.get("sub")
        if not username:
            logger.warning("Token missing 'sub' claim")
            return None

        return username

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def create_session(username: str) -> AdminSession:
    """
    Create a new admin session.
    """
    token = generate_token(username)
    now = time.time()
    expires_at = now + (TOKEN_EXPIRE_MINUTES * 60)

    session = AdminSession(
        username=username,
        token=token,
        created_at=now,
        expires_at=expires_at,
        last_activity=now,
    )

    _sessions[token] = session
    logger.info(f"Created session for user: {username}")

    return session


def get_session(token: str) -> Optional[AdminSession]:
    """
    Get a session by token.

    Returns None if session doesn't exist or is expired.
    """
    session = _sessions.get(token)

    if not session:
        return None

    # Check if session is expired
    if time.time() > session.expires_at:
        # Clean up expired session
        _sessions.pop(token, None)
        logger.info(f"Expired session removed for user: {session.username}")
        return None

    # Update last activity
    session.last_activity = time.time()

    return session


def invalidate_session(token: str) -> bool:
    """
    Invalidate a session (logout).

    Returns True if session was found and removed.
    """
    session = _sessions.pop(token, None)
    if session:
        logger.info(f"Session invalidated for user: {session.username}")
        return True
    return False


def clean_expired_sessions():
    """
    Remove all expired sessions from the store.

    Call this periodically to prevent memory leaks.
    """
    now = time.time()
    expired_tokens = [
        token for token, session in _sessions.items()
        if now > session.expires_at
    ]

    for token in expired_tokens:
        session = _sessions.pop(token)
        logger.info(f"Cleaned expired session for user: {session.username}")

    if expired_tokens:
        logger.info(f"Cleaned {len(expired_tokens)} expired sessions")


async def verify_admin(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> str:
    """
    FastAPI dependency to verify admin authentication.

    Usage:
        @app.get("/admin/protected")
        async def protected_route(username: str = Depends(verify_admin)):
            return {"message": f"Hello, admin {username}!"}

    Raises:
        HTTPException: If authentication fails

    Returns:
        str: The authenticated username
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Strip "Bearer " prefix if present
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    # Verify token
    session = get_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session.username


def login(username: str, password: str) -> LoginResponse:
    """
    Login handler - accepts any username/password for demo purposes.

    Args:
        username: Username
        password: Password (ignored for demo)

    Returns:
        LoginResponse with token
    """
    # Demo mode: Accept any username/password
    # In production, verify credentials against a database

    if not username or len(username.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty",
        )

    # Create session
    session = create_session(username)

    expires_in = int(session.expires_at - session.created_at)

    logger.info(f"User logged in: {username}")

    return LoginResponse(
        success=True,
        token=session.token,
        username=username,
        expires_in=expires_in,
    )


def logout(token: str) -> LogoutResponse:
    """
    Logout handler - invalidates the session.

    Args:
        token: Session token

    Returns:
        LogoutResponse
    """
    success = invalidate_session(token)

    if success:
        return LogoutResponse(
            success=True,
            message="Logged out successfully",
        )
    else:
        return LogoutResponse(
            success=False,
            message="Session not found or already expired",
        )


def verify_session(token: str) -> VerifyResponse:
    """
    Verify if a session is still valid.

    Args:
        token: Session token

    Returns:
        VerifyResponse with validity status
    """
    session = get_session(token)

    if session:
        expires_in = int(session.expires_at - time.time())
        return VerifyResponse(
            valid=True,
            username=session.username,
            expires_in=expires_in,
        )
    else:
        return VerifyResponse(valid=False)


# Background task to clean expired sessions
def start_session_cleaner():
    """
    Start a background task to periodically clean expired sessions.

    In production, use a proper task scheduler like APScheduler or Celery.
    """
    import asyncio

    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            clean_expired_sessions()

    # Return the coroutine without starting it
    # The caller should add it to the event loop
    return cleanup_loop()
