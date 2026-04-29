from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, get_optional_user
from app.models.activation import UserModelActivation
from app.models.model import Model
from app.models.user import User
from app.schemas.model import ActivationResponse, ModelDetailResponse, ModelResponse

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# Seed data for initial models
SEED_MODELS = [
    {"model_id": "qwen3.6-plus", "name": "Qwen3.6-Plus", "model_type": "Chat", "provider": "通义", "description": "通义千问3.6增强版，适用于复杂对话和推理任务", "sort_order": 1},
    {"model_id": "qwen3-max", "name": "Qwen3-Max", "model_type": "Chat", "provider": "通义", "description": "通义千问3旗舰版，最强综合能力", "sort_order": 2},
    {"model_id": "kimi-k2.6", "name": "Kimi-K2.6", "model_type": "Chat", "provider": "月之暗面", "description": "Kimi K2.6大模型，擅长长文本理解和生成", "sort_order": 3},
    {"model_id": "deepseek-v4-pro", "name": "DeepSeek-V4-Pro", "model_type": "Chat", "provider": "DeepSeek", "description": "DeepSeek V4专业版，高性价比推理模型", "sort_order": 4},
]


def seed_models_if_empty(db: Session) -> None:
    if db.query(Model).count() == 0:
        for m in SEED_MODELS:
            db.add(Model(**m))
        db.commit()


@router.get("/", response_model=list[ModelResponse])
def list_models(db: Session = Depends(get_db)):
    seed_models_if_empty(db)
    return db.query(Model).filter(Model.is_available == True).order_by(Model.sort_order).all()


@router.get("/activated", response_model=list[ActivationResponse])
def list_activated_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserModelActivation)
        .filter(
            UserModelActivation.user_id == current_user.id,
            UserModelActivation.status == "active",
        )
        .all()
    )


@router.get("/{model_id}", response_model=ModelDetailResponse)
def get_model_detail(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    seed_models_if_empty(db)
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    resp = ModelDetailResponse.model_validate(model)
    # Check activation status if user is authenticated
    if current_user:
        activation = (
            db.query(UserModelActivation)
            .filter(
                UserModelActivation.user_id == current_user.id,
                UserModelActivation.model_id == model_id,
                UserModelActivation.status == "active",
            )
            .first()
        )
        resp.activated = activation is not None
    return resp


@router.post("/{model_id}/activate", response_model=ActivationResponse)
def activate_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    model = db.query(Model).filter(Model.model_id == model_id, Model.is_available == True).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or unavailable")

    existing = (
        db.query(UserModelActivation)
        .filter(
            UserModelActivation.user_id == current_user.id,
            UserModelActivation.model_id == model_id,
            UserModelActivation.status == "active",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Model already activated")

    activation = UserModelActivation(
        user_id=current_user.id,
        model_id=model_id,
        status="active",
    )
    db.add(activation)
    db.commit()
    db.refresh(activation)
    return activation


@router.post("/{model_id}/deactivate", response_model=ActivationResponse)
def deactivate_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activation = (
        db.query(UserModelActivation)
        .filter(
            UserModelActivation.user_id == current_user.id,
            UserModelActivation.model_id == model_id,
            UserModelActivation.status == "active",
        )
        .first()
    )
    if not activation:
        raise HTTPException(status_code=404, detail="No active activation found")

    activation.status = "deactivated"
    activation.deactivated_at = datetime.utcnow()
    db.commit()
    db.refresh(activation)
    return activation
