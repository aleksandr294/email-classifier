import pathlib
import typing
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components.core import database
from components.email import repository as email_repository
from components.email import schemas as email_schemas
from components.email.enums import EmailCategory, EmailStatus
from components.email.service import ClassifyEmailService


@pytest.fixture
def mock_parser() -> MagicMock:
    parser = MagicMock()
    parser.process = AsyncMock(return_value=email_schemas.ParsedEmailSchema(subject="Test Email"))
    return parser


@pytest.mark.asyncio
async def test_high_confidence_classification_sets_classified_status(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
    mock_parser: MagicMock,
):
    async with database_manager.connect() as conn:
        email = await builder_email(conn=conn)
        await conn.commit()

    mock_provider = MagicMock()
    mock_provider.classify = AsyncMock(
        return_value=email_schemas.ClassificationResultSchema(
            category=EmailCategory.SPAM,
            confidence=0.95,
            reasoning="Clear spam indicators detected",
            signals=["fake prize", "urgency language", "suspicious link"],
        )
    )

    async with database_manager.connect() as conn:
        service = ClassifyEmailService(
            email_processor=mock_parser,
            llm_provider=mock_provider,
            email_repo=email_repo,
        )
        with patch.object(pathlib.Path, "read_bytes", return_value=b"fake eml content"):
            result = await service.process(email, conn)

        assert result.status == EmailStatus.CLASSIFIED
        assert result.category == EmailCategory.SPAM
        assert result.confidence == 0.95
        assert result.reviewed is False


@pytest.mark.asyncio
async def test_low_confidence_classification_stays_pending(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
    mock_parser: MagicMock,
):
    async with database_manager.connect() as conn:
        email = await builder_email(conn=conn)
        await conn.commit()

    mock_provider = MagicMock()
    mock_provider.classify = AsyncMock(
        return_value=email_schemas.ClassificationResultSchema(
            category=EmailCategory.PERSONAL,
            confidence=0.40,
            reasoning="Ambiguous signals, not confident",
            signals=[],
        )
    )

    async with database_manager.connect() as conn:
        service = ClassifyEmailService(
            email_processor=mock_parser,
            llm_provider=mock_provider,
            email_repo=email_repo,
        )
        with patch.object(pathlib.Path, "read_bytes", return_value=b"fake eml content"):
            result = await service.process(email, conn)

        assert result.status == EmailStatus.PENDING
        assert result.reviewed is False


@pytest.mark.asyncio
async def test_second_pass_marks_as_reviewed_and_classified(
    database_manager: database.DatabaseMngr,
    email_repo: email_repository.EmailRepository,
    builder_email: typing.Callable,
    mock_parser: MagicMock,
):
    async with database_manager.connect() as conn:
        email = await builder_email(conn=conn, classified_spam=True)
        await conn.commit()

    mock_provider = MagicMock()
    mock_provider.classify = AsyncMock(
        return_value=email_schemas.ClassificationResultSchema(
            category=EmailCategory.PHISHING,
            confidence=0.45,
            reasoning="Second look still inconclusive, but forced classified",
            signals=["suspicious link"],
        )
    )

    async with database_manager.connect() as conn:
        email_refreshed = await email_repo.get_by_id(id=email.id, conn=conn)
        service = ClassifyEmailService(
            email_processor=mock_parser,
            llm_provider=mock_provider,
            email_repo=email_repo,
        )
        with patch.object(pathlib.Path, "read_bytes", return_value=b"fake eml content"):
            result = await service.process(email_refreshed, conn)

        assert result.status == EmailStatus.CLASSIFIED
        assert result.reviewed is True
