import typing

import pytest
from fastapi import testclient as fastapi_test
from sqlalchemy.ext import asyncio as sa_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from components.core import database
from components.core.testing_database import (
    get_test_async_engine,
    get_test_async_session_context_manager_from_async_engine,
)
from components.email.factories import EmailFactory
from components.email.models import Email
from components.email.parser import EmailParser
from components.email.repository import EmailRepository
from main import app


@pytest.fixture
async def async_engine() -> typing.AsyncIterator[AsyncEngine]:
    async with get_test_async_engine() as engine:
        yield engine


@pytest.fixture
def database_manager(async_engine: AsyncEngine) -> database.DatabaseMngr:
    database_mgr = database.DatabaseMngr()
    special_context_manager = get_test_async_session_context_manager_from_async_engine(async_engine)
    database_mgr.__setattr__("get_session", lambda: special_context_manager)
    return database_mgr


@pytest.fixture
def test_client(database_manager: database.DatabaseMngr) -> fastapi_test.TestClient:
    app.dependency_overrides[database.DatabaseMngr.get_db] = lambda: database_manager
    app.middleware_stack = app.build_middleware_stack()
    return fastapi_test.TestClient(app)


@pytest.fixture
def builder_email() -> typing.Callable:
    async def create_email(conn: sa_asyncio.AsyncSession, **params: dict) -> Email:
        EmailFactory._meta.sqlalchemy_session = conn
        email = EmailFactory(**params)
        return email

    return create_email


@pytest.fixture
def email_repo() -> EmailRepository:
    return EmailRepository.get()


@pytest.fixture
def parser() -> EmailParser:
    return EmailParser.get()
