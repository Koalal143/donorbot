from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.organizer import Organizer


class OrganizerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, organizer: Organizer) -> Organizer:
        self.session.add(organizer)
        await self.session.commit()
        return organizer

    async def get_all(self) -> list[Organizer]:
        query = select(Organizer).order_by(Organizer.name)
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_paginated(self, page: int, page_size: int) -> tuple[list[Organizer], int]:
        count_query = select(func.count(Organizer.id))
        total_count = await self.session.scalar(count_query) or 0

        query = select(Organizer).order_by(Organizer.name).offset(page * page_size).limit(page_size)
        result = await self.session.scalars(query)
        organizers = list(result.all())

        return organizers, total_count

    async def get_by_id(self, organizer_id: int) -> Organizer | None:
        query = select(Organizer).where(Organizer.id == organizer_id)
        result = await self.session.scalars(query)
        return result.first()

    async def get_by_name(self, name: str) -> Organizer | None:
        query = select(Organizer).where(Organizer.name == name)
        result = await self.session.scalars(query)
        return result.first()
