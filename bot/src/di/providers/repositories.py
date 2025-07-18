from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.donor import DonorRepository
from src.repositories.organizer import OrganizerRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_donor_repository(self, session: AsyncSession) -> DonorRepository:
        return DonorRepository(session)

    @provide
    def get_organizer_repository(self, session: AsyncSession) -> OrganizerRepository:
        return OrganizerRepository(session)
