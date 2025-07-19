from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Content(Base):
    __tablename__ = "content"

    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("organizers.id"), nullable=False)
