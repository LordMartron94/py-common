from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class DefaultHoornLogOutput(HoornLogOutputInterface):
    def __init__(self):
        super().__init__(is_child=True)

    def output(self, hoorn_log: HoornLog) -> None:
        print(hoorn_log.formatted_message)
