from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import ChangePasswordRequest
from app.utils.security import hash_password, verify_password
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.put("/password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码不正确")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"detail": "密码修改成功"}
