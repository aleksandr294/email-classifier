import datetime
import typing
from unittest.mock import AsyncMock, patch

import pytest
import sqlalchemy as sa

from components.core import database
from components.email import models
from components.email import repository as email_repository
from components.email import schemas as email_schemas
from components.email.enums import EmailStatus


@pytest.mark.asyncio
async def test_create_returns_existing_when_concurrent_insert_wins_the_race(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
):
    async with database_manager.connect() as conn:
        existing = await builder_email(conn=conn, content_hash="a" * 64)
        await conn.commit()
        existing_id = existing.id

    data = email_schemas.CreateEmailSchema(file_path="/tmp/x", content_hash="a" * 64)
    async with database_manager.connect() as conn:
        real_find = email_repo._find
        # the "check" step still sees nothing (the other request has not committed yet), the INSERT then conflicts
        with patch.object(email_repo, "_find", AsyncMock(side_effect=[None, await real_find(models.Email.id == existing_id, conn)])):
            instance, created = await email_repo.create(data, conn)

        assert created is False
        assert instance.id == existing_id
        # the session must stay usable after the conflict
        assert (await conn.execute(sa.select(sa.func.count()).select_from(models.Email))).scalar_one() == 1


@pytest.mark.asyncio
async def test_create_new_email(database_manager: database.DatabaseMngr, email_repo: email_repository.EmailRepository):
    data = email_schemas.CreateEmailSchema(file_path="/tmp/x", content_hash="b" * 64)
    async with database_manager.connect() as conn:
        instance, created = await email_repo.create(data, conn)
        await conn.commit()

    assert created is True
    assert instance.status == EmailStatus.PENDING


@pytest.mark.asyncio
async def test_claim_pending_marks_email_processing_and_releases_transaction(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
):
    async with database_manager.connect() as conn:
        await builder_email(conn=conn)
        await conn.commit()

    async with database_manager.connect() as conn:
        claimed = await email_repo.claim_pending(conn)
        assert claimed.status == EmailStatus.PROCESSING
        assert not conn.in_transaction()  # no open transaction/locks while the LLM is called

    async with database_manager.connect() as conn:
        assert await email_repo.claim_pending(conn) is None  # nothing left to claim


@pytest.mark.asyncio
async def test_reset_stale_processing_only_returns_old_records(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
):
    async with database_manager.connect() as conn:
        stale = await builder_email(conn=conn, status=EmailStatus.PROCESSING)
        fresh = await builder_email(conn=conn, status=EmailStatus.PROCESSING)
        await conn.commit()
        stale_id, fresh_id = stale.id, fresh.id
        await conn.execute(
            sa.update(models.Email)
            .where(models.Email.id == stale_id)
            .values(updated_stamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=60))
        )
        await conn.commit()

    async with database_manager.connect() as conn:
        assert await email_repo.reset_stale_processing(conn, older_than_minutes=15) == 1

    async with database_manager.connect() as conn:
        assert (await email_repo.get_by_id(stale_id, conn)).status == EmailStatus.PENDING
        assert (await email_repo.get_by_id(fresh_id, conn)).status == EmailStatus.PROCESSING
