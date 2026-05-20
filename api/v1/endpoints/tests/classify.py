import io
import typing
import uuid

import fastapi
import pytest
from fastapi import testclient as fastapi_test

from components.core import database
from components.email.constants import SPAM_EML


@pytest.mark.asyncio
async def test_post_classify_new_file_returns_201(test_client: fastapi_test.TestClient):
    response = test_client.post(
        "/api/v1/classify/",
        files={"file": ("spam.eml", io.BytesIO(SPAM_EML), "message/rfc822")},
    )
    assert response.status_code == fastapi.status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["reviewed"] is False


@pytest.mark.asyncio
async def test_post_classify_duplicate_file_returns_200(test_client: fastapi_test.TestClient):
    first = test_client.post(
        "/api/v1/classify/",
        files={"file": ("spam.eml", io.BytesIO(SPAM_EML), "message/rfc822")},
    )
    second = test_client.post(
        "/api/v1/classify/",
        files={"file": ("spam.eml", io.BytesIO(SPAM_EML), "message/rfc822")},
    )
    assert first.status_code == fastapi.status.HTTP_201_CREATED
    assert second.status_code == fastapi.status.HTTP_200_OK
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_post_classify_invalid_extension_returns_422(test_client: fastapi_test.TestClient):
    response = test_client.post(
        "/api/v1/classify/",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_classify_empty_file_returns_422(test_client: fastapi_test.TestClient):
    response = test_client.post(
        "/api/v1/classify/",
        files={"file": ("empty.eml", io.BytesIO(b""), "message/rfc822")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_classify_existing_record_returns_200(
    builder_email: typing.Callable,
    test_client: fastapi_test.TestClient,
    database_manager: database.DatabaseMngr,
):
    async with database_manager.connect() as conn:
        email = await builder_email(conn=conn)
        await conn.commit()

    response = test_client.get(f"/api/v1/classify/{str(email.id)}/")
    assert response.status_code == fastapi.status.HTTP_200_OK
    assert response.json()["id"] == str(email.id)


@pytest.mark.asyncio
async def test_get_classify_unknown_id_returns_404(test_client: fastapi_test.TestClient):
    response = test_client.get(f"/api/v1/classify/{uuid.uuid4()}/")
    assert response.status_code == fastapi.status.HTTP_404_NOT_FOUND
