import asyncio

from components.core.config import get_config
from components.core.database import DatabaseMngr
from components.core.logger import get_logger, setup_logging
from components.email.enums import EmailStatus
from components.email.repository import EmailRepository

logger = get_logger(__name__)

config = get_config()


async def run(db: DatabaseMngr = DatabaseMngr.get_db(), email_repo: EmailRepository = EmailRepository.get()) -> None:

    logger.info("Retry worker started")

    while True:
        try:
            async with db.connect() as conn:
                emails = await email_repo.get_failed_and_block(conn)
                for email in emails:
                    logger.info(f"Retrying email id={email.id}")
                    email.status = EmailStatus.PENDING
                    email.category = None
                    email.confidence = None
                    email.reasoning = None
                    email.signals = None
                await conn.commit()
                if emails:
                    logger.info(f"Reset {len(emails)} emails to pending")

                stale = await email_repo.reset_stale_processing(conn, config.STALE_PROCESSING_MINUTES)
                if stale:
                    logger.info(f"Returned {stale} stale processing emails to pending")
        except Exception:
            logger.exception("Worker error")

        await asyncio.sleep(config.RETRY_WORKER_PAUSE_SECONDS)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(run())
