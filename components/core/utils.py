import hashlib
import os
import typing
from email import policy
from email.parser import BytesParser

import aiofiles
import fastapi
from starlette.datastructures import UploadFile

from components.core.config import get_config

config = get_config()


async def get_eml_hash(file: typing.Union[bytes, UploadFile]) -> str:
    data = await file.read() if isinstance(file, UploadFile) else file
    return hashlib.sha256(data).hexdigest()


async def upload_file(file: UploadFile, file_hash: str) -> str:
    folder = config.BASE_DIR / config.FILES_FOLDER
    folder.mkdir(parents=True, exist_ok=True)

    file_path = os.path.join(folder, file_hash)

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            await out_file.write(chunk)

    return file_path


async def validate_eml(content: bytes) -> None:
    try:
        BytesParser(policy=policy.default).parsebytes(content)
    except Exception:
        raise fastapi.HTTPException(
            status_code=422,
            detail="Invalid .eml file",
        )
