import re
import unicodedata
import pandas as pd

from ..constants import COMMON_LOGGING_PREFIX


class StringUtils:
    """Utility class for string related operations."""
    # Precompile regex patterns once at class‐load
    _DIACRITICS_PATTERN = re.compile(r"[\u0300-\u036F]")
    _PUNCT_PATTERN      = re.compile(r"[^\w\s]")
    _UNDERSCORE_PATTERN = re.compile(r"_")
    _WS_COLLAPSE       = re.compile(r"\s+")

    def __init__(self, logger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.StringUtils"
        self._logger.trace("Successfully initialized...", separator=self._separator)

    def normalize_field(self, original_string: str) -> str:
        """Normalizes a single string to lowercase, strips diacritics, collapses whitespace, and preserves all scripts."""
        if not isinstance(original_string, str):
            return ""

        self._logger.trace(f"Normalizing string [{original_string}]", separator=self._separator)

        # 1) lowercase
        s = original_string.lower()

        # 2) decompose Unicode to separate base chars + diacritics
        s = unicodedata.normalize("NFKD", s)

        # 3) strip combining marks (diacritics) only
        s = "".join(ch for ch in s if not unicodedata.combining(ch))

        # 4) replace any punctuation or symbols with space
        s = self._PUNCT_PATTERN.sub(" ", s)

        # 5) underscores → space
        s = self._UNDERSCORE_PATTERN.sub(" ", s)

        # 6) collapse multiple spaces and trim
        s = self._WS_COLLAPSE.sub(" ", s).strip()

        return s

    def normalize_series(self, series: pd.Series) -> pd.Series:
        """
        Vectorized normalization of a pandas Series of strings:
        - lowercase
        - unicode NFKD decomposition
        - strip combining diacritics
        - replace punctuation/symbols & underscores with space
        - collapse whitespace and trim
        Non-string or NaN values become empty strings.
        """
        s = series.fillna("").astype(str)

        # lowercase & unicode decomposition
        s = s.str.lower().str.normalize("NFKD")

        # strip diacritics (combining marks)
        # Note: this has to be done with .apply because .str.replace doesn't see combining marks
        s = s.apply(lambda txt: self._DIACRITICS_PATTERN.sub("", txt))

        # punctuation → space
        s = s.str.replace(self._PUNCT_PATTERN, " ", regex=True)

        # underscores → space
        s = s.str.replace(self._UNDERSCORE_PATTERN, " ", regex=True)

        # collapse whitespace & trim
        s = (
            s.str.replace(self._WS_COLLAPSE, " ", regex=True)
            .str.strip()
        )

        return s
