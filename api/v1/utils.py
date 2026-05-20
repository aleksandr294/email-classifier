import fastapi
import magic

from components.core.config import get_config

config = get_config()


async def validate_eml_file(file: fastapi.UploadFile) -> bytes:
    if not file.filename or not file.filename.endswith(".eml"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File must have .eml extension."
        )

    raw = await file.read(config.MAX_FILE_SIZE + 1)

    if not raw:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Empty file.")

    if len(raw) > config.MAX_FILE_SIZE:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File too large (max 10 MB)."
        )

    mime = magic.from_buffer(raw[:2048], mime=True)
    if mime not in ("message/rfc822", "text/plain"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Invalid file type: {mime}."
        )

    return raw


async def eml_file(
    file: fastapi.UploadFile = fastapi.File(..., description=".eml file to email"),
) -> tuple[fastapi.UploadFile, bytes]:
    raw = await validate_eml_file(file)
    return file, raw
