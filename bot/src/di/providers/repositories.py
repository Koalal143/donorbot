from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.donor import DonorRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_donor_repository(self, session: AsyncSession) -> DonorRepository:
        return DonorRepository(session)
