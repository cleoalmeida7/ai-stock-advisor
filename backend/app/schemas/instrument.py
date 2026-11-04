from pydantic import BaseModel


class InstrumentRead(BaseModel):
    id: str
    exchange: str
    symbol: str
    company_name: str
    data_source: str
    sector: str | None = None
