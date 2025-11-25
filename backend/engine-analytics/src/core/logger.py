import logging
import sys

# Robust, stdout-first logger for Engine A
class EngineALogger:
    def __init__(self, name: str = "engine-a"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - ENGINE-A - %(levelname)s - %(message)s"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        file_handler = logging.FileHandler("engine_a.log")
        file_handler.setFormatter(formatter)
        self.logger.handlers = [stream_handler, file_handler]

    def info(self, msg: str) -> None:
        self.logger.info(msg)
    def warning(self, msg: str) -> None:
        self.logger.warning(msg)
    def error(self, msg: str) -> None:
        self.logger.error(msg)
    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

logger = EngineALogger().logger
