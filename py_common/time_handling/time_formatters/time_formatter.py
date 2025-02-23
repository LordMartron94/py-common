from abc import ABC, abstractmethod


class ABCTimeFormatter(ABC):
    @abstractmethod
    def format(self, total_seconds: float, round_digits: int) -> str:
        """Formats time and rounds the seconds to the specified number of digits."""
