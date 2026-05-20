import json
import logging
import sys

from loguru import logger


def _serialize(record: dict) -> str:
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    if record["extra"]:
        subset["extra"] = record["extra"]
    if record["exception"] is not None:
        subset["exception"] = record["exception"]
    return json.dumps(subset, default=str)


def _json_sink(message: "loguru.Message") -> None:
    sys.stdout.write(_serialize(message.record) + "\n")
    sys.stdout.flush()


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(_json_sink, level=level, enqueue=True)

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


def get_logger(name: str = "") -> "loguru.Logger":
    return logger.bind(module=name) if name else logger
