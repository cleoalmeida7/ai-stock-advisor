from datetime import date

from pydantic import BaseModel


class PricePoint(BaseModel):
    price_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float
    adjusted_close: float
    volume: int | None
