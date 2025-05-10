from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit
from PyQt5.QtCore import QTimer, QCoreApplication
from threading import Thread
from queue import Queue, Empty
import sys

from ansi2html import Ansi2HTMLConverter

from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class WindowedHoornLogOutput(HoornLogOutputInterface):
    def __init__(self, max_separator_length: int = 30, base_batch_size: int = 100, max_batch_size: int = 1000):
        self._max_separator_length = max_separator_length
        self._base_batch_size = base_batch_size
        self._max_batch_size = max_batch_size
        self._log_queue = Queue()
        # Ensure QApplication runs in main thread; only queue lines here
        self._window_thread = Thread(target=self._start_gui, daemon=True)
        self._window_thread.start()
        super().__init__(is_child=True)

    def output(self, hoorn_log: HoornLog, encoding: str = "utf-8") -> None:
        if "${ignore=default}" in hoorn_log.formatted_message:
            return

        line = f"[{hoorn_log.separator:<{self._max_separator_length}}] {hoorn_log.formatted_message}"
        self._log_queue.put(line)

    def save(self):
        # No file-based saving for this output
        self._window.close()

    def _start_gui(self):
        # Initialize the QApplication
        self._app = QApplication(sys.argv)

        # Create and show the log window
        self._window = LogWindow(self._log_queue, self._base_batch_size, self._max_batch_size)
        self._window.show()

        # Execute the app, catching external exit calls
        try:
            exit_code = self._app.exec_()
        except SystemExit:
            # External exit() or sys.exit() called
            exit_code = 0
        finally:
            # Ensure the QApplication is quit
            if QCoreApplication.instance():
                QCoreApplication.instance().quit()

        # Exit the thread with the application's exit code
        sys.exit(exit_code)

    def _on_exit(self):
        # Optional: perform any required cleanup here
        print("Hoorn Log GUI is exiting.")


class LogWindow(QWidget):
    def __init__(self, log_queue: Queue, base_batch_size: int, max_batch_size: int):
        super().__init__()
        self.setWindowTitle("Hoorn Log Output")
        self.resize(800, 600)

        # Use QPlainTextEdit for efficient plain-text logging
        self.text_area = QPlainTextEdit(self)
        self.text_area.setReadOnly(True)
        # cap total lines to avoid infinite growth
        self.text_area.document().setMaximumBlockCount(10000)
        self.text_area.setStyleSheet("background-color: #343434; color: #EEEEEE;")

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        self.setLayout(layout)

        self.log_queue = log_queue
        self.base_batch_size = base_batch_size
        self.max_batch_size = max_batch_size
        self.ansi_converter = Ansi2HTMLConverter(dark_bg=True, inline=True)

        # Throttle updates: process dynamically-sized batches every poll interval
        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self._poll_queue)
        self.timer.start(100)

    def _poll_queue(self):
        # Adapt batch size based on queue length
        qsize = self.log_queue.qsize()
        dynamic_batch = min(
            self.base_batch_size + (qsize // 1000) * self.base_batch_size,
            self.max_batch_size
        )

        lines = []
        for _ in range(dynamic_batch):
            try:
                lines.append(self.log_queue.get_nowait())
            except Empty:
                break
        if not lines:
            return

        # Batch-convert ANSI to HTML and append once
        html = "".join(self._convert_ansi_to_html(line) for line in lines)
        self.text_area.appendHtml(html)

        # Auto-scroll to bottom
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _convert_ansi_to_html(self, line: str) -> str:
        html_body = self.ansi_converter.convert(line, full=False)
        return f'<pre style="margin:0">{html_body}</pre>'
