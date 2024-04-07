from enum import Enum


class LogType(Enum):
    DEBUG = "DEBUG",
    INFO = "INFO",
    WARNING = "WARNING",
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    DEFAULT = "DEFAULT"
