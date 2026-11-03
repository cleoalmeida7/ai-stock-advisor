from dataclasses import dataclass

from fastapi import Header, HTTPException, status
from supabase_auth.errors import AuthError

from app.db.supabase_client import get_anon_client


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    access_token: str


def get_current_user(authorization: str | None = Header(default=None)) -> AuthContext:
    """
    The backend's real auth gate. Every protected route depends on this.
    It independently calls Supabase's auth.get_user() with the caller's own
    token - it never trusts a frontend redirect, a client-supplied user id,
    or any claim that wasn't just verified against Supabase itself.
    See docs/architecture-decisions.md ADR-007.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        response = get_anon_client().auth.get_user(token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    if response is None or response.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return AuthContext(user_id=response.user.id, access_token=token)
