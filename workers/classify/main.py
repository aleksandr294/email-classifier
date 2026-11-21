import asyncio

from components.core.config import get_config
from components.core.database import DatabaseMngr
from components.core.logger import get_logger, setup_logging
from components.email.repository import EmailRepository
from components.email.service import ClassifyEmailService

logger = get_logger(__name__)

config = get_config()


async def run(
    db: DatabaseMngr = DatabaseMngr.get_db(),
    email_repo: EmailRepository = EmailRepository.get(),
    classify_service: ClassifyEmailService = ClassifyEmailService.get(),
) -> None:

    logger.info("Classify worker started")

    while True:
        try:
            async with db.connect() as conn:
                email = await email_repo.claim_pending(conn)
            if email:
                # new session: no transaction/lock is held while waiting for the LLM
                async with db.connect() as conn:
                    await classify_service.process(email, conn)
                logger.info(f"Email id={email.id} was classified")
        except Exception:
            logger.exception("Worker error")
        await asyncio.sleep(config.CLASSIFY_WORKER_PAUSE_SECONDS)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(run())
