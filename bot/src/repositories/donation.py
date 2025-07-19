from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, func, select

from src.models.donation import Donation
from src.models.donor import Donor
from src.models.donor_day import DonorDay

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession


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

    async def get_donor_day_statistics(self, donor_day_id: int) -> dict[str, int]:
        """Получить статистику по конкретному донорскому дню"""
        from sqlalchemy import func

        # Общее количество регистраций
        total_query = select(func.count(Donation.id)).where(Donation.donor_day_id == donor_day_id)
        total_result = await self.session.scalar(total_query)
        total_registrations = total_result or 0

        # Количество подтвержденных донаций
        confirmed_query = select(func.count(Donation.id)).where(
            Donation.donor_day_id == donor_day_id, Donation.is_confirmed
        )
        confirmed_result = await self.session.scalar(confirmed_query)
        confirmed_donations = confirmed_result or 0

        return {
            "total_registrations": total_registrations,
            "confirmed_donations": confirmed_donations,
        }

    async def get_organizer_statistics_by_date_range(
        self, organizer_id: int, start_date, end_date
    ) -> list[dict[str, Any]]:
        """Получить статистику организатора за период по всем донорским дням"""
        from sqlalchemy import func

        from src.models.donor_day import DonorDay

        query = (
            select(
                DonorDay.id.label("donor_day_id"),
                DonorDay.event_datetime.label("event_date"),
                func.count(Donation.id).label("total_registrations"),
                func.sum(func.cast(Donation.is_confirmed, Integer)).label("confirmed_donations"),
            )
            .select_from(DonorDay)
            .outerjoin(Donation, DonorDay.id == Donation.donor_day_id)
            .where(
                DonorDay.organizer_id == organizer_id,
                func.date(DonorDay.event_datetime) >= start_date.date() if hasattr(start_date, "date") else start_date,
                func.date(DonorDay.event_datetime) <= end_date.date() if hasattr(end_date, "date") else end_date,
            )
            .group_by(DonorDay.id, DonorDay.event_datetime)
            .order_by(DonorDay.event_datetime)
        )

        result = await self.session.execute(query)
        statistics = []

        for row in result:
            statistics.append(
                {
                    "donor_day_id": row.donor_day_id,
                    "event_date": row.event_date,
                    "total_registrations": row.total_registrations or 0,
                    "confirmed_donations": row.confirmed_donations or 0,
                }
            )

        return statistics

    async def get_all_organizer_donor_days(self, organizer_id: int) -> list[dict[str, Any]]:
        """Получить все донорские дни организатора"""
        from sqlalchemy import func

        from src.models.donor_day import DonorDay
        from src.models.organizer import Organizer

        query = (
            select(
                DonorDay.id.label("donor_day_id"),
                DonorDay.event_datetime.label("event_date"),
                Organizer.name.label("organizer_name"),
                func.count(Donation.id).label("total_registrations"),
                func.sum(func.cast(Donation.is_confirmed, Integer)).label("confirmed_donations"),
            )
            .select_from(DonorDay)
            .join(Organizer, DonorDay.organizer_id == Organizer.id)
            .outerjoin(Donation, DonorDay.id == Donation.donor_day_id)
            .where(DonorDay.organizer_id == organizer_id)
            .group_by(DonorDay.id, DonorDay.event_datetime, Organizer.name)
            .order_by(DonorDay.event_datetime.desc())
        )

        result = await self.session.execute(query)
        statistics = []

        for row in result:
            statistics.append(
                {
                    "donor_day_id": row.donor_day_id,
                    "event_date": row.event_date,
                    "organizer_name": row.organizer_name,
                    "total_registrations": row.total_registrations or 0,
                    "confirmed_donations": row.confirmed_donations or 0,
                }
            )

        return statistics

    async def find_donor_day_by_date_and_organizer(self, event_date: datetime, organizer_id: int) -> int | None:
        """Найти ID донорского дня по дате и организатору"""
        from src.models.donor_day import DonorDay

        query = select(DonorDay.id).where(
            DonorDay.organizer_id == organizer_id, func.date(DonorDay.event_datetime) == event_date.date()
        )

        return await self.session.scalar(query)

    async def get_confirmed_donations_by_organizer(self, organizer_id: int) -> list[dict[str, Any]]:
        """Получить все подтвержденные донации организатора с данными доноров"""
        from src.models.donor import Donor
        from src.models.donor_day import DonorDay
        from src.models.organizer import Organizer

        query = (
            select(
                Donor.full_name.label("donor_name"),
                DonorDay.event_datetime.label("donation_date"),
                Organizer.name.label("organizer_name"),
            )
            .select_from(Donation)
            .join(Donor, Donation.donor_id == Donor.id)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .join(Organizer, DonorDay.organizer_id == Organizer.id)
            .where(DonorDay.organizer_id == organizer_id, Donation.is_confirmed)
            .order_by(DonorDay.event_datetime.desc(), Donor.full_name)
        )

        result = await self.session.execute(query)
        donations = []

        for row in result:
            donations.append(
                {
                    "donor_name": row.donor_name,
                    "donation_date": row.donation_date,
                    "organizer_name": row.organizer_name,
                }
            )

        return donations

    async def get_participants_by_donor_day(self, donor_day_id: int) -> list[dict[str, Any]]:
        """Получить всех участников конкретного донорского дня"""
        from src.models.donor import Donor

        query = (
            select(
                Donation.id.label("donation_id"),
                Donation.is_confirmed.label("is_confirmed"),
                Donor.id.label("donor_id"),
                Donor.full_name.label("donor_name"),
                Donor.phone_number.label("phone_number"),
                Donor.is_bone_marrow_donor.label("is_bone_marrow_donor"),
            )
            .select_from(Donation)
            .join(Donor, Donation.donor_id == Donor.id)
            .where(Donation.donor_day_id == donor_day_id)
            .order_by(Donor.full_name)
        )

        result = await self.session.execute(query)
        participants = []

        for row in result:
            participants.append(
                {
                    "donation_id": row.donation_id,
                    "donor_id": row.donor_id,
                    "donor_name": row.donor_name,
                    "phone_number": row.phone_number,
                    "is_confirmed": row.is_confirmed,
                    "is_bone_marrow_donor": row.is_bone_marrow_donor,
                }
            )

        return participants

    async def update_donation_status(self, donation_id: int, is_confirmed: bool) -> bool:
        """Обновить статус подтверждения донации"""
        donation = await self.session.get(Donation, donation_id)
        if donation:
            donation.is_confirmed = is_confirmed
            await self.session.commit()
            return True
        return False

    async def get_by_donor_and_donor_day(self, donor_id: int, donor_day_id: int) -> Donation | None:
        """Найти донацию по донору и донорскому дню"""
        query = select(Donation).where(Donation.donor_id == donor_id, Donation.donor_day_id == donor_day_id)
        return await self.session.scalar(query)

    async def create_donation(self, donor_id: int, donor_day_id: int) -> Donation:
        """Создать новую донацию"""
        from src.models.donor_day import DonorDay

        # Получаем organizer_id из донорского дня
        donor_day = await self.session.get(DonorDay, donor_day_id)
        if not donor_day:
            msg = "Донорский день не найден"
            raise ValueError(msg)

        donation = Donation(
            donor_id=donor_id, donor_day_id=donor_day_id, organizer_id=donor_day.organizer_id, is_confirmed=False
        )

        self.session.add(donation)
        await self.session.commit()
        await self.session.refresh(donation)
        return donation
