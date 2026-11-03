from typing import Protocol

from postgrest.exceptions import APIError
from supabase import Client

from app.repositories.exceptions import DuplicateHoldingError
from app.schemas.holding import HoldingCreate, HoldingRead
from app.schemas.instrument import InstrumentRead

UNIQUE_VIOLATION = "23505"


class PortfolioRepository(Protocol):
    def list_holdings(self, user_id: str) -> list[HoldingRead]: ...

    def create_holding(self, user_id: str, data: HoldingCreate, instrument: InstrumentRead) -> HoldingRead: ...

    def delete_holding(self, user_id: str, holding_id: str) -> bool: ...


class SupabasePortfolioRepository:
    """
    Every method here runs through a client authenticated as `user_id`'s own
    JWT (see app.db.supabase_client.get_user_scoped_client). The explicit
    .eq("user_id", user_id) filters are defense-in-depth, not the primary
    boundary - Postgres RLS is what actually prevents cross-user access,
    even if a filter here were ever missed. See ADR-005 and ADR-007.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def list_holdings(self, user_id: str) -> list[HoldingRead]:
        result = (
            self._client.table("holdings")
            .select("*, instrument:instruments(*)")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        return [self._map(row) for row in result.data]

    def create_holding(self, user_id: str, data: HoldingCreate, instrument: InstrumentRead) -> HoldingRead:
        payload = {
            "user_id": user_id,
            "instrument_id": data.instrument_id,
            "quantity": str(data.quantity),
            "average_buy_price": str(data.average_buy_price),
        }
        try:
            result = self._client.table("holdings").insert(payload).execute()
        except APIError as exc:
            if exc.code == UNIQUE_VIOLATION:
                raise DuplicateHoldingError(
                    f"User already holds instrument {data.instrument_id}"
                ) from exc
            raise

        row = result.data[0]
        row["instrument"] = instrument.model_dump()
        return self._map(row)

    def delete_holding(self, user_id: str, holding_id: str) -> bool:
        result = (
            self._client.table("holdings")
            .delete()
            .eq("id", holding_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(result.data) > 0

    @staticmethod
    def _map(row: dict) -> HoldingRead:
        instrument_data = row.pop("instrument")
        return HoldingRead(instrument=InstrumentRead(**instrument_data), **row)
