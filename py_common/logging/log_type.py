from enum import Enum


class LogType(Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    DEFAULT = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6

    def __ge__(self, other):
        return self.value >= other.value

    def __gt__(self, other):
        return self.value > other.value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.name)
