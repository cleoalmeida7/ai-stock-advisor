from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_anon_client() -> Client:
    """
    Unscoped client, anon key only. Used strictly for verifying a caller's
    JWT via auth.get_user() - never for reading or writing application
    tables, since it carries no user identity for RLS to key off of.
    """
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_user_scoped_client(access_token: str) -> Client:
    """
    A fresh client per request, authenticated as the requesting user via
    their own JWT. Postgres RLS enforces ownership on every query made with
    this client - there is no service-role / RLS-bypassing client in this
    codebase. See docs/architecture-decisions.md ADR-005.
    """
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
