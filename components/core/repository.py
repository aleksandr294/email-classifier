import typing
import uuid

import pydantic
import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_asyncio

from components.core import database


class BaseRepository:
    def __init__(self, model: typing.Type[database.Base]) -> None:
        self.model = model

    async def get_by_id(self, id: uuid.UUID, conn: sa_asyncio.AsyncSession) -> typing.Optional[database.Base]:
        query = sa.select(self.model).where(self.model.id == id)
        result = await conn.execute(query)

        instance = result.scalar_one_or_none()
        return instance

    async def get_by_ids(
        self, ids: typing.List[uuid.UUID], conn: sa_asyncio.AsyncSession
    ) -> typing.List[database.Base]:
        query = sa.select(self.model).where(self.model.id.in_(ids))
        result = await conn.execute(query)
        return result.scalars().all()

    async def get_all(self, conn: sa_asyncio.AsyncSession) -> typing.List[database.Base]:
        query = sa.select(self.model)
        result = await conn.execute(query)
        return result.scalars().all()

    async def create(self, data: typing.Any, conn: sa_asyncio.AsyncSession) -> database.Base:
        instance = self.model(**data.model_dump())
        conn.add(instance)
        return instance

    async def bulk_create(self, data: typing.Any, conn: sa_asyncio.AsyncSession) -> None:
        instances = [self.model(**item.model_dump()) for item in data]
        conn.add_all(instances)

    async def update(
        self, instance: database.Base, data: pydantic.BaseModel, conn: sa_asyncio.AsyncSession
    ) -> database.Base:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)

        await conn.commit()
        await conn.refresh(instance)
        return instance

    async def delete(self, instance: database.Base, conn: sa_asyncio.AsyncSession) -> None:
        await conn.delete(instance)

    async def get_or_create(
        self, data: typing.Any, conn: sa_asyncio.AsyncSession, conditional: typing.Any
    ) -> typing.Tuple[database.Base, bool]:
        query = sa.select(self.model).where(conditional)
        result = await conn.execute(query)

        instance = result.scalar_one_or_none()
        if not instance:
            instance = self.model(**data.model_dump())
            conn.add(instance)
            return instance, True

        return instance, False
