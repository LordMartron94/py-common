from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class DefaultHoornLogOutput(HoornLogOutputInterface):
    def __init__(self):
        super().__init__(is_child=True)

    def output(self, hoorn_log: HoornLog, encoding="utf-8") -> None:
        print(f"[{hoorn_log.separator:<30}] {hoorn_log.formatted_message}")
