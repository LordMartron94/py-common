from typing import Dict, Tuple, Union, List

from ...logging.formatting.log_formatter_interface import HoornLogFormatterInterface
from ...logging.hoorn_log import HoornLog
from ...logging.log_type import LogType
from ...utils.color_helper import ColorHelper


class HoornLogColorFormatter(HoornLogFormatterInterface):
    """
    A formatter that formats log messages in a colorful way based on the log type.
    """
    def __init__(self):
        self._color_helper = ColorHelper()

        # Precompute color strings and store them directly in a list indexed by LogType value
        default_color = ("#9B9B9B", None)
        self._color_map: List[Tuple[str, Union[str, None]]] = [default_color] * len(LogType)  # Pre-fill with default

        # Explicitly assign colors for each log type
        self._color_map[LogType.TRACE.value] = ("#4682B4", None)
        self._color_map[LogType.DEBUG.value] = ("#079B00", None)
        self._color_map[LogType.INFO.value] = ("#9B9B9B", None)
        self._color_map[LogType.WARNING.value] = ("#FFA300", None)
        self._color_map[LogType.ERROR.value] = ("#FF0000", None)
        self._color_map[LogType.CRITICAL.value] = ("#FFFFFF", "#FF0000")

        super().__init__(is_child=True)

    def format(self, hoorn_log: HoornLog) -> str:
        # Directly access the precomputed color tuple
        text_color_hex, background_color_hex = self._color_map[hoorn_log.log_type.value]

        return self._color_helper.colorize_string(
            hoorn_log.formatted_message,
            text_color_hex,
            background_color_hex
        )
