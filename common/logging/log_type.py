from enum import Enum


class LogType(Enum):
    DEBUG = "DEBUG",
    INFO = "INFO",
    DEFAULT = "DEFAULT",
    WARNING = "WARNING",
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
