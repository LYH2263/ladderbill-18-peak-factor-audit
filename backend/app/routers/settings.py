from fastapi import APIRouter, HTTPException, Query

from app.schemas.entities import PeakFactorUpdate
from app.services.billing_service import BillingService, UnchangedPeakFactorError

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings():
    with BillingService() as svc:
        return svc.settings_map()


@router.put("/settings/peak_factor")
def put_peak_factor(body: PeakFactorUpdate):
    with BillingService() as svc:
        try:
            entry = svc.update_peak_factor(body.value, body.operator, body.remark)
        except UnchangedPeakFactorError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return {"ok": True, "audit": entry}


@router.get("/settings/peak_factor/audits")
def get_peak_factor_audits(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    with BillingService() as svc:
        return svc.list_peak_factor_audits(page, page_size)
