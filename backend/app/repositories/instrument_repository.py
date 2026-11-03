from typing import Protocol

from supabase import Client

from app.schemas.instrument import InstrumentRead


class InstrumentRepository(Protocol):
    def search(self, query: str, limit: int = 20) -> list[InstrumentRead]: ...

    def get(self, instrument_id: str) -> InstrumentRead | None: ...


class SupabaseInstrumentRepository:
    """
    Reads the instrument master through the caller's own RLS-scoped client.
    No admin/service-role path exists here - instruments is public-read for
    any authenticated user at the database level (see migration 0001).
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def search(self, query: str, limit: int = 20) -> list[InstrumentRead]:
        q = self._client.table("instruments").select("*")
        if query:
            escaped = query.replace("%", "").replace(",", "")
            q = q.or_(f"symbol.ilike.%{escaped}%,company_name.ilike.%{escaped}%")
        result = q.limit(limit).execute()
        return [InstrumentRead(**row) for row in result.data]

    def get(self, instrument_id: str) -> InstrumentRead | None:
        result = self._client.table("instruments").select("*").eq("id", instrument_id).maybe_single().execute()
        if result is None or result.data is None:
            return None
        return InstrumentRead(**result.data)
