from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.enums.donor_type import DonorType
from src.models.donation import Donation
from src.models.donor import Donor
from src.models.donor_day import DonorDay

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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

    async def search_by_full_name(self, full_name: str) -> list[Donor]:
        query = select(Donor).where(Donor.full_name.ilike(f"%{full_name}%"))
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_registered_donors_by_full_name(self, full_name: str) -> list[Donor]:
        query = select(Donor).where(Donor.full_name.ilike(f"%{full_name}%"), Donor.telegram_id.is_not(None))
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_registered_donor_by_phone(self, phone_number: str) -> Donor | None:
        query = select(Donor).where(Donor.phone_number == phone_number, Donor.telegram_id.is_not(None))
        result = await self.session.scalars(query)
        return result.first()

    async def update_donor_data(
        self,
        donor_id: int,
        full_name: str,
        phone_number: str,
        donor_type: DonorType,
        student_group: str | None = None,
        *,
        is_bone_marrow_donor: bool = False,
    ) -> Donor | None:
        donor = await self.get_by_id(donor_id)
        if donor:
            donor.full_name = full_name
            donor.phone_number = phone_number
            donor.donor_type = donor_type
            donor.student_group = student_group if donor_type == DonorType.STUDENT else None
            donor.is_bone_marrow_donor = is_bone_marrow_donor
            await self.session.commit()
            await self.session.refresh(donor)
        return donor

    async def check_user_exists_by_phone(self, phone_number: str) -> bool:
        query = select(Donor).where(Donor.phone_number == phone_number, Donor.telegram_id.is_not(None))
        result = await self.session.scalars(query)
        return result.first() is not None

    async def check_user_exists_by_full_name(self, full_name: str) -> list[Donor]:
        query = select(Donor).where(Donor.full_name.ilike(f"%{full_name}%"), Donor.telegram_id.is_not(None))
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_user_by_phone_not_donor(self, phone_number: str) -> Donor | None:
        query = select(Donor).where(
            Donor.phone_number == phone_number, Donor.telegram_id.is_not(None), Donor.donor_type.is_(None)
        )
        result = await self.session.scalars(query)
        return result.first()

    async def convert_user_to_donor(
        self,
        user_id: int,
        donor_type: DonorType,
        student_group: str | None = None,
        *,
        is_bone_marrow_donor: bool = False,
    ) -> Donor | None:
        user = await self.get_by_id(user_id)
        if user and user.telegram_id and not user.donor_type:
            user.donor_type = donor_type
            user.student_group = student_group if donor_type == DonorType.STUDENT else None
            user.is_bone_marrow_donor = is_bone_marrow_donor
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def create_donor_from_existing_user(
        self,
        phone_number: str,
        full_name: str,
        donor_type: DonorType,
        student_group: str | None = None,
        *,
        is_bone_marrow_donor: bool = False,
    ) -> Donor | None:
        existing_user = await self.get_user_by_phone_not_donor(phone_number)
        if existing_user:
            existing_user.full_name = full_name
            existing_user.donor_type = donor_type
            existing_user.student_group = student_group if donor_type == DonorType.STUDENT else None
            existing_user.is_bone_marrow_donor = is_bone_marrow_donor
            await self.session.commit()
            await self.session.refresh(existing_user)
            return existing_user
        return None

    async def get_bone_marrow_donors(self) -> list[Donor]:
        query = select(Donor).where(Donor.is_bone_marrow_donor)
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_donors_registered_for_upcoming_donor_day(self, organizer_id: int) -> list[Donor]:
        """Получить доноров, зарегистрированных на ближайшую дату ДД конкретного организатора"""
        query = (
            select(Donor)
            .join(Donation, Donor.id == Donation.donor_id)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(
                DonorDay.organizer_id == organizer_id,
                DonorDay.event_datetime >= datetime.now(UTC),
                Donor.telegram_id.is_not(None),
            )
            .distinct()
        )
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_donors_not_registered_for_upcoming_dates(self, organizer_id: int) -> list[Donor]:
        organizer_donors_query = (
            select(Donor.id)
            .join(Donation, Donor.id == Donation.donor_id)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(DonorDay.organizer_id == organizer_id, Donor.telegram_id.is_not(None))
            .distinct()
        )

        registered_for_upcoming_query = (
            select(Donor.id)
            .join(Donation, Donor.id == Donation.donor_id)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(DonorDay.organizer_id == organizer_id, DonorDay.event_datetime >= datetime.now(UTC))
            .distinct()
        )

        query = select(Donor).where(Donor.id.in_(organizer_donors_query), ~Donor.id.in_(registered_for_upcoming_query))
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_donors_registered_but_not_confirmed(self, organizer_id: int) -> list[Donor]:
        query = (
            select(Donor)
            .join(Donation, Donor.id == Donation.donor_id)
            .join(DonorDay, Donation.donor_day_id == DonorDay.id)
            .where(DonorDay.organizer_id == organizer_id, not Donation.is_confirmed, Donor.telegram_id.is_not(None))
            .distinct()
        )
        result = await self.session.scalars(query)
        return list(result.all())
