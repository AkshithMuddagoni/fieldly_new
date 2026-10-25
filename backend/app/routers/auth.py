import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

DEV_OTP = "482609"
# Dev OTP (482609) works locally, and on a deployed test site unless you set DEMO_MODE=false.
# Set DEMO_MODE=false once a real SMS provider (MSG91/Twilio) is wired in.
DEMO_OTP_ALLOWED = security.IS_LOCAL or os.getenv("DEMO_MODE", "true").lower() != "false"


def _send_otp(phone: str) -> None:
    print(f"[DEV OTP] Sending OTP {DEV_OTP} to +91{phone}")


@router.post("/request-otp")
def request_otp(payload: schemas.OTPRequest):
    if not DEMO_OTP_ALLOWED:
        raise HTTPException(503, "SMS OTP provider not configured (wire MSG91/Twilio first)")
    _send_otp(payload.phone)
    # dev_hint is returned only so the local/demo frontend can autofill it.
    # Remove this field once a real SMS provider is wired in.
    return {"message": "OTP sent", "dev_hint": DEV_OTP}


@router.post("/verify-otp", response_model=schemas.TokenOut)
def verify_otp(payload: schemas.OTPVerify, db: Session = Depends(get_db)):
    if not DEMO_OTP_ALLOWED or not secrets.compare_digest(payload.otp, DEV_OTP):
        raise HTTPException(400, "Invalid OTP")
    if payload.role not in ("customer", "provider"):
        raise HTTPException(400, "Invalid role")

    user = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if not user:
        user = models.User(phone=payload.phone, name=payload.name, role=payload.role)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif payload.name and not user.name:
        user.name = payload.name
        db.commit()

    token = security.create_access_token(user.id, user.role)
    return schemas.TokenOut(access_token=token, user_id=user.id, role=user.role, name=user.name)
