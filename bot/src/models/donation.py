from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Boolean

from src.models.base import Base


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id"), nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("organizers.id"), nullable=False)
    donor_day_id: Mapped[int] = mapped_column(ForeignKey("donor_days.id", ondelete="CASCADE"), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
