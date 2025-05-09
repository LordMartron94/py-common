from pathlib import Path
from typing import Any, Optional, Dict
from ..constants import COMMON_LOGGING_PREFIX
from ..json_storage import JsonStorageHandler
from ..logging import HoornLogger


class CacheBuilder:
    """Helper class for building a persistent cache and interacting with it, utilizing a search-tree structure for efficiency."""

    def __init__(self, logger: HoornLogger, cache_json_path: Path, tree_separator: str = "."):
        self._logger: HoornLogger = logger
        self._cache_json_path: Path = cache_json_path
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.CacheBuilder"

        self._json_storage: JsonStorageHandler = JsonStorageHandler(logger, cache_json_path, allow_non_exist=True)
        self._tree_separator: str = tree_separator

        # Initialize cache if it does not exist
        if not self._json_storage.exists():
            self._json_storage.write({})

        self._search_tree: Dict = self._build_search_tree()

        self._logger.trace("Successfully initialized.", separator=self._separator)

    def _build_search_tree(self) -> Dict:
        """Builds a search-tree like structure from the cache dictionary."""
        cache = self._json_storage.read()

        tree = {}
        for key, value in cache.items():
            parts = key.split(self._tree_separator)
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
        return tree

    def _sort_cache(self, cache: dict) -> dict:
        """Returns a sorted version of the cache dictionary."""
        return dict(sorted(cache.items()))

    def get(self, key: str) -> Optional[Any]:
        cache = self._json_storage.read()
        if not cache:
            return None

        parts = key.split(self._tree_separator)
        node = self._search_tree
        for part in parts:
            if part in node:
                node = node[part]
            else:
                return None
        return node

    def set(self, key: str, value: Any) -> bool:
        cache = self._json_storage.read() or {}
        cache[key] = value

        # Sort cache before writing
        sorted_cache = self._sort_cache(cache)

        result = self._json_storage.write(sorted_cache)
        self._search_tree = self._build_search_tree()
        return result

    def delete(self, key: str) -> bool:
        cache = self._json_storage.read()
        if cache and key in cache:
            del cache[key]
            sorted_cache = self._sort_cache(cache)
            result = self._json_storage.write(sorted_cache)
            self._search_tree = self._build_search_tree()
            return result

        return False
