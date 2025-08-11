from pathlib import Path
from typing import List

from ..logging import HoornLogger


class PathNotFoundError(BaseException):
    def __init__(self, logger: HoornLogger, separator: str, path: Path):
        message: str = f"Path '{path}' does not exist."
        logger.error(message, separator=separator)
        super().__init__(message)

class PathNotAFileError(BaseException):
    def __init__(self, logger: HoornLogger, separator: str, path: Path):
        message: str = f"Path '{path}' is not a file."
        logger.error(message, separator=separator)
        super().__init__(message)

class PathNotTheRightExtensionError(BaseException):
    def __init__(self, logger: HoornLogger, separator: str, path: Path, extensions: List[str]):
        message: str = f"Path '{path}' with extension '{path.suffix}' does not have a valid extension. Possible: {', '.join(extensions)}."
        logger.error(message, separator=separator)
        super().__init__(message)
