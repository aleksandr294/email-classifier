import contextlib
import typing

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from components.core import database


@contextlib.asynccontextmanager
async def get_test_async_engine() -> typing.AsyncIterator[AsyncEngine]:
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    yield async_engine

    async with async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)

    await async_engine.dispose()


def get_test_async_session_context_manager_from_async_engine(
    async_engine: AsyncEngine,
) -> typing.Callable[[], contextlib.AbstractAsyncContextManager[AsyncSession]]:
    @contextlib.asynccontextmanager
    async def get_session_context_manager() -> typing.AsyncIterator[AsyncSession]:
        async_session_maker = sessionmaker(
            async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        async with async_session_maker() as session:
            yield session

    return get_session_context_manager
