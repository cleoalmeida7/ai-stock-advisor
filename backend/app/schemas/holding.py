from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.instrument import InstrumentRead


class HoldingCreate(BaseModel):
    """
    Deliberately has no user_id field: the owner is always the authenticated
    caller resolved server-side by app.core.auth, never a client-supplied value.
    """

    instrument_id: str
    quantity: Decimal = Field(gt=0)
    average_buy_price: Decimal = Field(gt=0)


class HoldingRead(BaseModel):
    id: str
    quantity: Decimal
    average_buy_price: Decimal
    total_cost: Decimal
    source: str
    created_at: datetime
    instrument: InstrumentRead
