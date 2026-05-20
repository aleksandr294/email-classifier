import pathlib

from sqlalchemy.ext import asyncio as sa_asyncio

from components.email import models as classify_models
from components.email.constants import MIN_CONFIDENCE_VALUE
from components.email.enums import EmailStatus
from components.email.parser import EmailParser
from components.email.repository import EmailRepository
from components.email.schemas import ClassificationResultSchema, ParsedEmailSchema
from components.third_party.anthropic.provider import AnthropicProvider


class ClassifyEmailService:
    def __init__(
        self,
        email_processor: EmailParser = EmailParser.get(),
        llm_provider: AnthropicProvider = AnthropicProvider.get(),
        email_repo: EmailRepository = EmailRepository.get(),
    ) -> None:
        self.email_parser = email_processor
        self.llm_provider = llm_provider
        self.email_repo = email_repo

    @classmethod
    def get(cls) -> "ClassifyEmailService":
        return cls()

    async def process(self, email: classify_models.Email, conn: sa_asyncio.AsyncSession) -> classify_models.Email:
        try:
            raw_bytes = pathlib.Path(email.file_path).read_bytes()
            parsed = await self.email_parser.process(raw_bytes)
            result = await self.llm_provider.classify(self._build_prompt(parsed))
            return await self._save_result(email, result, conn)
        except Exception:
            email.status = EmailStatus.FAILED
            await conn.commit()
            raise

    async def _save_result(
        self,
        email: classify_models.Email,
        result: ClassificationResultSchema,
        conn: sa_asyncio.AsyncSession,
    ) -> classify_models.Email:

        is_second_pass = email.category is not None
        high_confidence = result.confidence >= MIN_CONFIDENCE_VALUE

        email.status = EmailStatus.CLASSIFIED if (high_confidence or is_second_pass) else EmailStatus.PENDING
        email.reviewed = is_second_pass
        email.category = result.category
        email.confidence = result.confidence
        email.reasoning = result.reasoning
        email.signals = result.signals
        await conn.commit()
        # await conn.refresh(email)
        return email

    def _build_prompt(self, parsed: ParsedEmailSchema) -> str:
        lines = []
        if parsed.sender:
            lines.append(f"From: {parsed.sender}")
        if parsed.recipients:
            lines.append(f"To: {', '.join(parsed.recipients)}")
        if parsed.date:
            lines.append(f"Date: {parsed.date}")
        if parsed.subject:
            lines.append(f"Subject: {parsed.subject}")
        lines.append("")
        if parsed.body_plain:
            lines.append(parsed.body_plain)
        elif parsed.body_html:
            lines.append(parsed.body_html)
        return "\n".join(lines)
