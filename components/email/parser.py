import email.policy
import typing
from email.message import EmailMessage
from email.parser import BytesParser
from typing import cast

from components.email.schemas import AttachmentSchema, ParsedEmailSchema


class EmailParser:

    @classmethod
    def get(cls) -> "EmailParser":
        return cls()

    async def process(self, raw_bytes: bytes) -> ParsedEmailSchema:
        parsed = await self._parse(raw_bytes)
        return parsed

    async def _parse(self, raw_bytes: bytes) -> ParsedEmailSchema:
        message = cast(EmailMessage, BytesParser(policy=email.policy.default).parsebytes(raw_bytes))

        return ParsedEmailSchema(
            subject=message.get("Subject"),
            sender=message.get("From"),
            recipients=self._extract_recipients(message),
            date=message.get("Date"),
            body_plain=self._extract_body(message, "text/plain"),
            body_html=self._extract_body(message, "text/html"),
            attachments=self._extract_attachments(message),
            headers=dict(message.items()),
        )

    @staticmethod
    def _extract_recipients(message: EmailMessage) -> list[str]:
        to = message.get("To") or ""
        return [r.strip() for r in to.split(",") if r.strip()]

    @staticmethod
    def _extract_body(message: EmailMessage, content_type: str) -> typing.Optional[str]:
        for part in message.walk():
            if part.get_content_type() == content_type and part.get_content_disposition() != "attachment":
                return part.get_content()
        return None

    @staticmethod
    def _extract_attachments(message: EmailMessage) -> list[AttachmentSchema]:
        result = []
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                result.append(
                    AttachmentSchema(
                        filename=part.get_filename(),
                        content_type=part.get_content_type(),
                        payload=part.get_payload(decode=True) or b"",
                    )
                )
        return result
