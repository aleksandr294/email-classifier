import uuid

import fastapi
from sqlalchemy.ext import asyncio as sa_asyncio

from api.v1.utils import eml_file
from components.core import database
from components.core.utils import get_eml_hash, upload_file
from components.email import repository as classify_repository
from components.email import schemas as classify_schemas

router = fastapi.APIRouter(
    prefix="/classify",
    tags=["classify"],
)


@router.post("/", response_model=classify_schemas.EmailDetailSchema)
async def create_classifier(
    payload: tuple[fastapi.UploadFile, bytes] = fastapi.Depends(eml_file),
    conn: sa_asyncio.AsyncSession = fastapi.Depends(database.get_session),
    email_repo: classify_repository.EmailRepository = fastapi.Depends(classify_repository.EmailRepository.get),
) -> fastapi.responses.JSONResponse:

    file, raw = payload

    await file.seek(0)
    content_hash = await get_eml_hash(raw)
    file_path = await upload_file(file, content_hash)

    data = classify_schemas.CreateEmailSchema(file_path=file_path, content_hash=content_hash)
    instance, is_created = await email_repo.create(data, conn)

    if is_created:
        await conn.commit()
        await conn.refresh(instance)

    status_code = fastapi.status.HTTP_201_CREATED if is_created else fastapi.status.HTTP_200_OK
    content = classify_schemas.EmailDetailSchema.model_validate(instance).model_dump(mode="json")

    return fastapi.responses.JSONResponse(content=content, status_code=status_code)


@router.get("/{id}/", status_code=fastapi.status.HTTP_200_OK, response_model=classify_schemas.EmailDetailSchema)
async def get_instance(
    id: uuid.UUID,
    conn: sa_asyncio.AsyncSession = fastapi.Depends(database.get_session),
    email_repo: classify_repository.EmailRepository = fastapi.Depends(classify_repository.EmailRepository.get),
) -> fastapi.responses.JSONResponse:
    instance = await email_repo.get_by_id(id=id, conn=conn)
    if instance is None:
        return fastapi.responses.JSONResponse(dict(detail="Not Found"), status_code=fastapi.status.HTTP_404_NOT_FOUND)

    content = classify_schemas.EmailDetailSchema.model_validate(instance).model_dump(mode="json")

    return fastapi.responses.JSONResponse(content, status_code=fastapi.status.HTTP_200_OK)
