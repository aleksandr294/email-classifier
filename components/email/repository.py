import typing

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_asyncio

from components.core import repository
from components.email import enums as classify_enums
from components.email import models as classify_models


class EmailRepository(repository.BaseRepository):
    @classmethod
    def get(cls) -> "EmailRepository":
        return cls(model=classify_models.Email)

    async def create(self, data: typing.Any, conn: sa_asyncio.AsyncSession) -> "Email":

        conditional = self.model.content_hash == data.content_hash
        return await self.get_or_create(data=data, conditional=conditional, conn=conn)

    async def get_failed_and_block(self, conn: sa_asyncio.AsyncSession, limit: int = 10) -> list[classify_models.Email]:
        result = await conn.execute(
            sa.select(self.model)
            .where(self.model.status == classify_enums.EmailStatus.FAILED)
            .order_by(self.model.updated_stamp)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def get_pending_and_block(self, conn: sa_asyncio.AsyncSession) -> typing.Optional[classify_models.Email]:
        result = await conn.execute(
            sa.select(self.model)
            .where(self.model.status == classify_enums.EmailStatus.PENDING)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()
