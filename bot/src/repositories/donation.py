from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donation import Donation
from src.models.donor import Donor
from src.models.donor_day import DonorDay


class DonationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, donation: Donation) -> Donation:
        self.session.add(donation)
        await self.session.commit()
        await self.session.refresh(donation)
        return donation

    async def get_by_donor_id(self, donor_id: int) -> Sequence[Donation]:
        result = await self.session.scalars(select(Donation).where(Donation.donor_id == donor_id))
        return result.all()

    async def get_donor_registrations_with_details(self, donor_id: int) -> Sequence[tuple[Donation, DonorDay]]:
        result = await self.session.execute(
            select(Donation, DonorDay)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(Donation.donor_id == donor_id)
            .order_by(DonorDay.event_datetime.asc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_donor_donations_with_details(self, donor_id: int) -> Sequence[tuple[Donation, DonorDay]]:
        result = await self.session.execute(
            select(Donation, DonorDay)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(Donation.donor_id == donor_id)
            .order_by(DonorDay.event_datetime.desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_donations_with_donors_by_donor_day(self, donor_day_id: int) -> Sequence[tuple[Donation, Donor]]:
        result = await self.session.execute(
            select(Donation, Donor)
            .join(Donor, Donation.donor_id == Donor.id)
            .where(Donation.donor_day_id == donor_day_id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_by_donor_day_id(self, donor_day_id: int) -> Sequence[Donation]:
        result = await self.session.scalars(select(Donation).where(Donation.donor_day_id == donor_day_id))
        return result.all()

    async def get_donor_registration(self, donor_id: int, donor_day_id: int) -> Donation | None:
        result = await self.session.scalars(
            select(Donation).where(Donation.donor_id == donor_id, Donation.donor_day_id == donor_day_id)
        )
        return result.first()

    async def confirm_donation(self, donation_id: int) -> Donation | None:
        result = await self.session.scalars(select(Donation).where(Donation.id == donation_id))
        donation = result.first()
        if donation:
            donation.is_confirmed = True
            await self.session.commit()
            await self.session.refresh(donation)
        return donation

    async def get_by_id(self, donation_id: int) -> Donation | None:
        result = await self.session.scalars(select(Donation).where(Donation.id == donation_id))
        return result.first()

    async def delete_donation(self, donation_id: int) -> bool:
        result = await self.session.scalars(select(Donation).where(Donation.id == donation_id))
        donation = result.first()
        if donation:
            await self.session.delete(donation)
            await self.session.commit()
            return True
        return False
