import datetime
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

    async def claim_pending(self, conn: sa_asyncio.AsyncSession) -> typing.Optional[classify_models.Email]:
        """Atomically take one pending email and mark it as processing.

        The row lock is held only for this short transaction, so the (slow) LLM call that follows
        never keeps a database transaction open. Crashed workers are recovered by `reset_stale_processing`.
        """
        result = await conn.execute(
            sa.select(self.model)
            .where(self.model.status == classify_enums.EmailStatus.PENDING)
            .order_by(self.model.created_stamp)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        email = result.scalar_one_or_none()
        if email is not None:
            email.status = classify_enums.EmailStatus.PROCESSING
            await conn.commit()
        return email

    async def reset_stale_processing(self, conn: sa_asyncio.AsyncSession, older_than_minutes: int) -> int:
        """Return emails abandoned in `processing` (e.g. worker crash) back to `pending`."""
        threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=older_than_minutes)
        result = await conn.execute(
            sa.select(self.model)
            .where(self.model.status == classify_enums.EmailStatus.PROCESSING)
            .where(self.model.updated_stamp < threshold)
            .with_for_update(skip_locked=True)
        )
        emails = list(result.scalars().all())
        for email in emails:
            email.status = classify_enums.EmailStatus.PENDING
        await conn.commit()
        return len(emails)
