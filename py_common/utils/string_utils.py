import re

import unicodedata

from ..constants import COMMON_LOGGING_PREFIX


class StringUtils:
    """Utility class for string related operations."""
    def __init__(self, logger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.StringUtils"
        self._logger.trace("Successfully initialized...", separator=self._separator)

    def normalize_field(self, original_string: str) -> str:
        """Normalizes a string to lowercase, strips diacritics, collapses whitespace, and preserves all scripts."""
        if not isinstance(original_string, str):
            return ""

        self._logger.trace(f"Normalizing string [{original_string}]", separator=self._separator)

        # 1) lowercase
        s = original_string.lower()

        # 2) decompose Unicode to separate base chars + diacritics
        s = unicodedata.normalize("NFKD", s)

        # 3) strip combining marks (diacritics) only
        s = "".join(ch for ch in s if not unicodedata.combining(ch))

        # 4) replace any punctuation or symbols (anything that isn't a word char or whitespace) with space
        #    \w under Unicode includes letters (from all scripts), digits, and underscore
        s = re.sub(r"[^\w\s]", " ", s)

        # 5) optionally replace underscores (if you don't want them)
        s = s.replace("_", " ")

        # 6) collapse multiple spaces and trim
        s = re.sub(r"\s+", " ", s).strip()

        return s
