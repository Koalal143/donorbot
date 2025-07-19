from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donor_day import DonorDay
from src.repositories.donation import DonationRepository


class DonorDayRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, donor_day: DonorDay) -> DonorDay:
        self.session.add(donor_day)
        await self.session.commit()
        await self.session.refresh(donor_day)
        return donor_day

    async def get_all_upcoming(self) -> Sequence[DonorDay]:
        result = await self.session.scalars(
            select(DonorDay).where(DonorDay.event_datetime >= datetime.now(UTC)).order_by(DonorDay.event_datetime.asc())
        )
        return result.all()

    async def get_by_id(self, donor_day_id: int) -> DonorDay | None:
        result = await self.session.scalars(select(DonorDay).where(DonorDay.id == donor_day_id))
        return result.first()

    async def get_by_organizer_id(self, organizer_id: int) -> Sequence[DonorDay]:
        result = await self.session.scalars(
            select(DonorDay).where(DonorDay.organizer_id == organizer_id).order_by(DonorDay.event_datetime.asc())
        )
        return result.all()

    async def delete_donor_day(self, donor_day_id: int) -> bool:
        result = await self.session.scalars(select(DonorDay).where(DonorDay.id == donor_day_id))
        donor_day = result.first()
        if donor_day:
            donation_repository = DonationRepository(self.session)

            donations = await donation_repository.get_by_donor_day_id(donor_day_id)

            for donation in donations:
                await self.session.delete(donation)

            await self.session.delete(donor_day)
            await self.session.commit()
            return True
        return False
