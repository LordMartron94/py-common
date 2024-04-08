from enum import Enum


class LogType(Enum):
    DEBUG = 0,
    INFO = 1,
    DEFAULT = 2,
    WARNING = 3,
    ERROR = 4
    CRITICAL = 5
