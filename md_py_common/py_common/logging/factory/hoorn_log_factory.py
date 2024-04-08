from datetime import datetime
from typing import List

from ...logging.formatting.log_color_formatter import HoornLogColorFormatter
from ...logging.formatting.log_formatter_interface import HoornLogFormatterInterface
from ...logging.formatting.log_text_formatter import HoornLogTextFormatter
from ...logging.hoorn_log import HoornLog
from ...logging.log_type import LogType


class HoornLogFactory:

    def create_hoorn_log(self, log_type: LogType, message: str) -> HoornLog:
        current_time = datetime.now()

        formatters: List[HoornLogFormatterInterface] = [
            HoornLogTextFormatter(),
            HoornLogColorFormatter(),
        ]

        hoorn_log = HoornLog(
            log_time=current_time,
            log_type=log_type,
            log_message=message,
            formatted_message=message
        )

        for formatter in formatters:
            hoorn_log.formatted_message = formatter.format(hoorn_log)

        return hoorn_log
