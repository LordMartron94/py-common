import re
import string
from typing import List

import unicodedata
import pandas as pd

from ..constants import COMMON_LOGGING_PREFIX


_PUNCT_TRANS = str.maketrans({c: " " for c in string.punctuation + "_"})
_WS_COLLAPSE = re.compile(r"\s+")

class StringUtils:
    """Utility class for string related operations."""
    # Precompile regex patterns once at class‐load
    _DIACRITICS_PATTERN = re.compile(r"[\u0300-\u036F]")
    _PUNCT_PATTERN      = re.compile(r"[^\w\s]")
    _UNDERSCORE_PATTERN = re.compile(r"_")

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
        s = _WS_COLLAPSE.sub(" ", s).strip()

        return s

    def normalize_series(self, series: pd.Series) -> pd.Series:
        """
        Normalize strings by lowercasing, removing diacritics,
        collapsing punctuation/whitespace—but preserving non-Latin letters.
        """
        s = series.fillna("").astype(str)

        # helper to do the core string pipeline on either Index or Series
        def _normalize(obj):
            return (
                obj
                .str.lower()
                .str.normalize("NFKD")
                # strip combining diacritics, preserving all other codepoints
                .str.replace(r"[\u0300-\u036f]+", "", regex=True)
                .str.translate(_PUNCT_TRANS)
                .str.replace(_WS_COLLAPSE, " ", regex=True)
                .str.strip()
            )

        # category shortcut when many repeats
        if s.nunique(dropna=True) < len(s) * 0.1:
            cat    = s.astype("category")
            cats   = cat.cat.categories
            normalized = _normalize(cats)
            labels, uniques = pd.factorize(normalized)
            new_codes = labels[cat.cat.codes]
            new_cat = pd.Categorical.from_codes(new_codes, categories=uniques)
            return pd.Series(new_cat).astype(str)

        # full-series pipeline
        return _normalize(s)

    def extract_primary_from_sequence(self, sequence: str) -> str:
        """Extracts the primary (first) from a sequence string by applying generic rules."""
        str_elements: List[str] = sequence.split(sep=',')
        return str_elements[0]
