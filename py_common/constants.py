import threading

CONSOLE_OUTPUT_LOCK: threading.Lock = threading.Lock()
COMMON_LOGGING_PREFIX: str = "Common"
