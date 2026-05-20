import sqlalchemy as sa

from components.core import models
from components.email.enums import EmailCategory, EmailStatus


class Email(models.BaseModel):
    __tablename__ = "classification_record"

    content_hash = sa.Column(sa.String(64), unique=True, nullable=False)
    file_path = sa.Column(sa.String(512), nullable=True)
    status = sa.Column(sa.Enum(EmailStatus), nullable=False, default=EmailStatus.PENDING)
    category = sa.Column(sa.Enum(EmailCategory), nullable=True)
    confidence = sa.Column(sa.Float, nullable=True)
    reasoning = sa.Column(sa.Text, nullable=True)
    signals = sa.Column(sa.JSON, nullable=True)
    reviewed = sa.Column(sa.Boolean, nullable=False, default=False)
