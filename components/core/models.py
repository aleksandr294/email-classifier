import uuid

import sqlalchemy as sa

from components.core import database


class BaseModel(database.Base):
    __abstract__ = True

    id = sa.Column(sa.UUID, default=uuid.uuid4, primary_key=True)
    created_stamp = sa.Column(sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"))
    updated_stamp = sa.Column(
        sa.TIMESTAMP,
        server_default=sa.text("CURRENT_TIMESTAMP"),
        onupdate=sa.text("CURRENT_TIMESTAMP"),
    )
