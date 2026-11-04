"""
In-memory stand-ins for the Supabase-backed repositories, used so the test
suite can run with no network access and no live Supabase project. See
docs/architecture-decisions.md (repository-protocol rationale) and the
Milestone 1 plan's verification section.
"""

import itertools
from datetime import date, datetime, timedelta, timezone

from app.market_data.provider import PriceBar
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


class FakePriceRepository:
    """
    Mirrors SupabasePriceRepository's contract (app/repositories/price_repository.py)
    without any network/DB access - used by /api/analysis and
    /api/portfolio/metrics route tests (Steps 5-6). The real Supabase-backed
    implementation is verified against the live project, same as every
    other repository's Supabase impl in this codebase (none of them get a
    direct unit test of their own query-building - see Milestone 1).
    """

    def __init__(self, bars_by_instrument: dict[str, list[PriceBar]] | None = None) -> None:
        self._bars_by_instrument = bars_by_instrument or {}

    def latest(self, instrument_id: str) -> PriceBar | None:
        bars = self._bars_by_instrument.get(instrument_id, [])
        return bars[-1] if bars else None

    def history(self, instrument_id: str, days: int) -> list[PriceBar]:
        cutoff = date.today() - timedelta(days=days)
        bars = self._bars_by_instrument.get(instrument_id, [])
        return [bar for bar in bars if bar.price_date >= cutoff]

    def set_bars(self, instrument_id: str, bars: list[PriceBar]) -> None:
        self._bars_by_instrument[instrument_id] = bars
