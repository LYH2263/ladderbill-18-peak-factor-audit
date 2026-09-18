from pydantic import BaseModel, Field


class BillRequest(BaseModel):
    account_id: int | None = None
    kwh: float = Field(ge=0)
    peak: bool = False
    persist: bool = True


class CompareRequest(BaseModel):
    kwh: float = Field(ge=0)
    persist: bool = False


class CalcRunOut(BaseModel):
    id: int
    kind: str
    account_id: int | None
    input_json: str
    result_json: str
    created_at: str


class PeakFactorUpdateRequest(BaseModel):
    new_value: float = Field(gt=0)
    operator: str = Field(default="admin", min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=200)
