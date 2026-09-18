from fastapi import APIRouter, HTTPException, Query

from app.schemas.billing import PeakFactorUpdateRequest
from app.services.billing_service import BillingService, SameFactorError

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings():
    with BillingService() as svc:
        return svc.settings_map()


@router.get("/settings/peak-factor")
def get_peak_factor():
    with BillingService() as svc:
        return svc.peak_factor_state()


@router.put("/settings/peak-factor")
def update_peak_factor(body: PeakFactorUpdateRequest):
    with BillingService() as svc:
        try:
            return svc.change_peak_factor(body.new_value, body.operator, body.note)
        except SameFactorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/settings/peak-factor/audits")
def list_peak_factor_audits(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    with BillingService() as svc:
        return svc.list_factor_audits(page, page_size)
