from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserModelActivation(Base):
    __tablename__ = "user_model_activations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    activated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
