from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import QTimer
from threading import Thread
from queue import Queue, Empty
import sys

from ansi2html import Ansi2HTMLConverter

from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class WindowedHoornLogOutput(HoornLogOutputInterface):
    def __init__(self, max_separator_length: int = 30):
        self._max_separator_length = max_separator_length
        self._log_queue = Queue()
        self._window_thread = Thread(target=self._start_gui, daemon=True)
        self._window_thread.start()
        super().__init__(is_child=True)

    def output(self, hoorn_log: HoornLog, encoding="utf-8") -> None:
        if "${ignore=default}" in hoorn_log.formatted_message:
            return

        line = f"[{hoorn_log.separator:<{self._max_separator_length}}] {hoorn_log.formatted_message}"
        self._log_queue.put(line)

    def _start_gui(self):
        self._app = QApplication(sys.argv)
        self._window = LogWindow(self._log_queue)
        self._window.show()
        self._app.exec_()


class LogWindow(QWidget):
    def __init__(self, log_queue: Queue):
        super().__init__()
        self.setWindowTitle("Hoorn Log Output")
        self.resize(800, 600)

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: #343434;")
        self.text_area.setAcceptRichText(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        self.setLayout(layout)

        self.log_queue = log_queue
        self.ansi_converter = Ansi2HTMLConverter(dark_bg=True, inline=True)

        self.timer = QTimer()
        self.timer.timeout.connect(self._poll_queue)
        self.timer.start(100)

    def _poll_queue(self):
        try:
            while True:
                log_line = self.log_queue.get_nowait()
                html = self._convert_ansi_to_html(log_line)
                self.text_area.append(html)
        except Empty:
            pass

    def _convert_ansi_to_html(self, line: str) -> str:
        html_body = self.ansi_converter.convert(line, full=False)
        return f'<pre style="margin:0">{html_body}</pre>'
