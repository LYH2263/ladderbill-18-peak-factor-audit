from pydantic import BaseModel, Field


class AccountOut(BaseModel):
    id: int
    name: str
    meter_no: str
    note: str | None = None


class TierOut(BaseModel):
    id: int
    up_to: float | None
    price: float
    sort_order: int


class ReadingOut(BaseModel):
    id: int
    account_id: int
    kwh: float
    peak: int


class PeakFactorUpdate(BaseModel):
    value: float = Field(gt=0)
    operator: str = Field(default="admin", min_length=1, max_length=64)
    remark: str | None = Field(default=None, max_length=200)
