from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from config import get_settings
from models.schemas import LeadRequest, LeadResponse
from rate_limit import limiter
from services.leads import save_lead

router = APIRouter()


@router.post("/lead", response_model=LeadResponse)
@limiter.limit(get_settings().rate_limit_lead)
async def create_lead(request: Request, payload: LeadRequest) -> LeadResponse:
    try:
        return save_lead(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Unable to save lead.") from exc
