from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donor import Donor


class DonorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, donor: Donor) -> Donor:
        self.session.add(donor)
        await self.session.commit()
        return donor

    async def get_by_phone_number(self, phone_number: str) -> Donor | None:
        query = select(Donor).where(Donor.phone_number == phone_number)
        result = await self.session.scalars(query)
        return result.first()

    async def get_by_id(self, donor_id: int) -> Donor | None:
        query = select(Donor).where(Donor.id == donor_id)
        result = await self.session.scalars(query)
        return result.first()

    async def get_by_telegram_id(self, telegram_id: int) -> Donor | None:
        query = select(Donor).where(Donor.telegram_id == telegram_id)
        result = await self.session.scalars(query)
        return result.first()

    async def update_telegram_id(self, donor_id: int, telegram_id: int) -> Donor | None:
        donor = await self.get_by_id(donor_id)
        if donor:
            donor.telegram_id = telegram_id
            await self.session.commit()
            await self.session.refresh(donor)
        return donor
