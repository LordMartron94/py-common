from queue import Queue, Empty
from threading import Thread
from typing import List

import dearpygui.dearpygui as dpg
from rich.text import Text

from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface

# TODO - Clean up and make more SOLID

class WindowedHoornLogOutput(HoornLogOutputInterface):
    def __init__(self, max_separator_length=30, base_batch_size=100, max_batch_size=1000):
        super().__init__(is_child=True)
        self._sep_len = max_separator_length
        self._base = base_batch_size
        self._max = max_batch_size
        self._queue: Queue[str] = Queue()
        self._line_counter = 0
        Thread(target=self._run_gui, daemon=True).start()

    def output(self, hoorn_log: HoornLog, encoding="utf-8"):
        msg = hoorn_log.formatted_message
        if "${ignore=default}" in msg:
            return
        prefix = f"[{hoorn_log.separator:<{self._sep_len}}]"
        self._queue.put(f"{prefix} {msg}")

    def save(self):
        dpg.stop_dearpygui()

    def _run_gui(self):
        dpg.create_context()
        dpg.create_viewport(title='Hoorn Log', width=800, height=600, disable_close=True)
        dpg.setup_dearpygui()
        with dpg.window(tag='log_win', no_title_bar=True, no_close=True, no_collapse=True):
            dpg.add_child_window(tag='log_region')
        dpg.set_primary_window('log_win', True)
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self._poll_queue()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def _poll_queue(self):
        batch = self._calculate_batch()
        new_lines = self._fetch_lines(batch)

        if not new_lines:
            return

        self._render_logs(new_lines)
        self._scroll_update_needed = True

    def _calculate_batch(self):
        batch = min(self._base + (self._queue.qsize() // 1000) * self._base, self._max)
        return batch

    def _fetch_lines(self, batch):
        new_lines = []
        for _ in range(batch):
            try:
                new_lines.append(self._queue.get_nowait())
            except Empty:
                break
        return new_lines

    def _render_logs(self, new_lines: List[str]):
        container_width = dpg.get_item_width('log_region')
        wrap_width = max(container_width - 10, 0)

        for idx, line in enumerate(new_lines):
            line_id = self._line_counter
            self._render_line(line, wrap_width, line_id)
            self._line_counter += 1

        # Track the last rendered log line
        if new_lines:
            last_line_tag = f"log_line_{self._line_counter - 1}"
            dpg.configure_item(last_line_tag, tracked=True, track_offset=1.0)

    def _render_line(self, line, wrap_width, line_id):
        with dpg.group(parent='log_region', horizontal=True, tag=f"log_line_{line_id}"):
            rich_text = Text.from_ansi(line)
            plain = rich_text.plain
            spans = rich_text.spans
            last_idx = 0

            for span in spans:
                start, end, style = span.start, span.end, span.style
                if start > last_idx:
                    seg = plain[last_idx:start]
                    dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width)
                seg = plain[start:end]
                r, g, b = (255, 255, 255) if not style.color else style.color.get_truecolor()
                dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width, color=(r, g, b))
                last_idx = end

            if last_idx < len(plain):
                seg = plain[last_idx:]
                dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width)

    def _update_scroll(self):
        max_scroll = dpg.get_y_scroll_max('log_region')
        dpg.set_y_scroll('log_region', max_scroll)
