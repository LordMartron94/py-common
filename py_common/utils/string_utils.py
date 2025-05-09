import re

import unicodedata

from ..constants import COMMON_LOGGING_PREFIX
from ..logging import HoornLogger


class StringUtils:
    """Utility class for string related operations."""
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.StringUtils"
        self._logger.trace("Successfully initialized...", separator=self._separator)

    def normalize_field(self, original_string: str) -> str:
        """Normalizes a string to lowercase, strips punctuation/accents, collapses whitespace."""
        if not isinstance(original_string, str):
            return ""

        self._logger.trace(f"Normalizing string [{original_string}]", separator=self._separator)

        normalized_string = original_string.lower()
        normalized_string = unicodedata.normalize("NFKD", normalized_string)
        normalized_string = re.sub(r"’", "'", normalized_string)
        normalized_string = re.sub(r"[^a-z0-9 ]", " ", normalized_string)
        normalized_string = re.sub(r"\s+", " ", normalized_string).strip()

        return normalized_string
