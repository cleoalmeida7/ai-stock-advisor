"""
In-memory stand-ins for the Supabase-backed repositories, used so the test
suite can run with no network access and no live Supabase project. See
docs/architecture-decisions.md (repository-protocol rationale) and the
Milestone 1 plan's verification section.
"""

import itertools
from datetime import datetime, timezone

from app.repositories.exceptions import DuplicateHoldingError
from app.schemas.holding import HoldingCreate, HoldingRead
from app.schemas.instrument import InstrumentRead

SEED_INSTRUMENTS = [
    InstrumentRead(id="11111111-1111-1111-1111-111111111111", exchange="NSE", symbol="RELIANCE", company_name="Reliance Industries Ltd", data_source="dev_seed"),
    InstrumentRead(id="22222222-2222-2222-2222-222222222222", exchange="NSE", symbol="TCS", company_name="Tata Consultancy Services Ltd", data_source="dev_seed"),
    InstrumentRead(id="33333333-3333-3333-3333-333333333333", exchange="NSE", symbol="INFY", company_name="Infosys Ltd", data_source="dev_seed"),
]


class FakeInstrumentRepository:
    def __init__(self, instruments: list[InstrumentRead] | None = None) -> None:
        self._instruments = {i.id: i for i in (instruments or SEED_INSTRUMENTS)}

    def search(self, query: str, limit: int = 20) -> list[InstrumentRead]:
        needle = query.lower()
        matches = [
            i
            for i in self._instruments.values()
            if needle in i.symbol.lower() or needle in i.company_name.lower()
        ]
        return matches[:limit]

    def get(self, instrument_id: str) -> InstrumentRead | None:
        return self._instruments.get(instrument_id)


class FakePortfolioRepository:
    def __init__(self) -> None:
        self._rows_by_user: dict[str, list[dict]] = {}
        self._id_counter = itertools.count(1)

    def list_holdings(self, user_id: str) -> list[HoldingRead]:
        return [self._to_read(row) for row in self._rows_by_user.get(user_id, [])]

    def create_holding(self, user_id: str, data: HoldingCreate, instrument: InstrumentRead) -> HoldingRead:
        rows = self._rows_by_user.setdefault(user_id, [])
        if any(r["instrument_id"] == data.instrument_id for r in rows):
            raise DuplicateHoldingError(f"User already holds instrument {data.instrument_id}")

        row = {
            "id": str(next(self._id_counter)),
            "instrument_id": data.instrument_id,
            "quantity": data.quantity,
            "average_buy_price": data.average_buy_price,
            "total_cost": data.quantity * data.average_buy_price,
            "source": "manual",
            "created_at": datetime.now(timezone.utc),
            "instrument": instrument,
        }
        rows.append(row)
        return self._to_read(row)

    def delete_holding(self, user_id: str, holding_id: str) -> bool:
        rows = self._rows_by_user.get(user_id, [])
        before = len(rows)
        self._rows_by_user[user_id] = [r for r in rows if r["id"] != holding_id]
        return len(self._rows_by_user[user_id]) < before

    @staticmethod
    def _to_read(row: dict) -> HoldingRead:
        return HoldingRead(
            id=row["id"],
            quantity=row["quantity"],
            average_buy_price=row["average_buy_price"],
            total_cost=row["total_cost"],
            source=row["source"],
            created_at=row["created_at"],
            instrument=row["instrument"],
        )
