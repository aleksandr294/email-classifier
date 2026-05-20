import typing
import uuid

import pydantic

from components.email import enums


class EmailRetrieveSchema(pydantic.BaseModel):
    id: uuid.UUID
    status: enums.EmailStatus
    category: typing.Optional[enums.EmailCategory]
    confidence: typing.Optional[float]
    reasoning: typing.Optional[str]
    signals: typing.Optional[list[str]]
    reviewed: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateEmailSchema(pydantic.BaseModel):
    file_path: str
    content_hash: str


class EmailDetailSchema(pydantic.BaseModel):
    id: uuid.UUID
    status: enums.EmailStatus
    category: typing.Optional[enums.EmailCategory]
    confidence: typing.Optional[float]
    reasoning: typing.Optional[str]
    signals: typing.Optional[list[str]]
    reviewed: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class ClassificationResultSchema(pydantic.BaseModel):
    category: enums.EmailCategory
    confidence: float
    reasoning: str
    signals: list[str]


class AttachmentSchema(pydantic.BaseModel):
    filename: typing.Optional[str] = None
    content_type: str
    payload: bytes


class ParsedEmailSchema(pydantic.BaseModel):
    subject: typing.Optional[str] = None
    sender: typing.Optional[str] = None
    recipients: list[str] = []
    date: typing.Optional[str] = None
    body_plain: typing.Optional[str] = None
    body_html: typing.Optional[str] = None
    attachments: list[AttachmentSchema] = []
    headers: dict[str, str] = {}
