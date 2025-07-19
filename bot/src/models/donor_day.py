from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from src.models.base import Base


class DonorDay(Base):
    __tablename__ = "donor_days"

    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("organizers.id"), nullable=False)
