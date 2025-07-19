from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

from src.models.content import Content


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, content: Content) -> Content:
        """Создать новый контент"""
        self.session.add(content)
        await self.session.commit()
        await self.session.refresh(content)
        return content

    async def get_by_id(self, content_id: int) -> Content | None:
        """Получить контент по ID"""
        return await self.session.get(Content, content_id)

    async def get_by_organizer_id(self, organizer_id: int) -> Sequence[Content]:
        """Получить весь контент конкретного организатора"""
        result = await self.session.scalars(
            select(Content).where(Content.organizer_id == organizer_id).order_by(Content.created_at.desc())
        )
        return result.all()

    async def get_all(self) -> Sequence[Content]:
        """Получить весь контент всех организаторов"""
        result = await self.session.scalars(select(Content).order_by(Content.created_at.desc()))
        return result.all()

    async def update(self, content: Content) -> Content:
        """Обновить контент"""
        await self.session.commit()
        await self.session.refresh(content)
        return content

    async def delete(self, content_id: int) -> bool:
        """Удалить контент"""
        content = await self.session.get(Content, content_id)
        if content:
            await self.session.delete(content)
            await self.session.commit()
            return True
        return False
