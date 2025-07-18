from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String

from src.models.base import Base


class Organizer(Base):
    __tablename__ = "organizers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
