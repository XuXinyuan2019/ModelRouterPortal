from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.recharge import RechargeRecord
from app.models.user import User
from app.schemas.balance import BalanceResponse, RechargeRecordResponse, RechargeRequest

router = APIRouter(prefix="/api/v1/balance", tags=["balance"])


@router.get("/", response_model=BalanceResponse)
def get_balance(current_user: User = Depends(get_current_user)):
    return BalanceResponse(balance=current_user.balance)


@router.post("/recharge", response_model=RechargeRecordResponse)
def submit_recharge(
    req: RechargeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    balance_before = current_user.balance
    current_user.balance += req.amount
    record = RechargeRecord(
        user_id=current_user.id,
        amount=req.amount,
        balance_before=balance_before,
        balance_after=current_user.balance,
        status="completed",
        remark=req.remark,
        completed_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/history", response_model=list[RechargeRecordResponse])
def recharge_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(RechargeRecord)
        .filter(RechargeRecord.user_id == current_user.id)
        .order_by(RechargeRecord.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/recharge/{record_id}/approve", response_model=RechargeRecordResponse)
def approve_recharge(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    record = db.query(RechargeRecord).filter(RechargeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Record is not pending")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    record.balance_before = user.balance
    user.balance += record.amount
    record.balance_after = user.balance
    record.status = "completed"
    record.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record
