from queue import Queue, Empty
from threading import Thread

import dearpygui.dearpygui as dpg
from rich.text import Text

from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface

class WindowedHoornLogOutput(HoornLogOutputInterface):
    def __init__(self, max_separator_length=30, base_batch_size=100, max_batch_size=1000):
        super().__init__(is_child=True)
        self._sep_len = max_separator_length
        self._base = base_batch_size
        self._max = max_batch_size
        self._queue: Queue[str] = Queue()
        self._buffer: list[str] = []
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
            dpg.add_child_window(tag='log_region', autosize_x=True, autosize_y=True, horizontal_scrollbar=True)
        dpg.set_primary_window('log_win', True)
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self._poll_queue()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def _poll_queue(self):
        batch = min(self._base + (self._queue.qsize() // 1000) * self._base, self._max)
        new_lines = []
        for _ in range(batch):
            try:
                new_lines.append(self._queue.get_nowait())
            except Empty:
                break
        if not new_lines:
            return

        self._buffer.extend(new_lines)
        if len(self._buffer) > 10000:
            self._buffer = self._buffer[-10000:]

        # Clear the log region
        for child in dpg.get_item_children('log_region', slot=1) or []:
            dpg.delete_item(child)

        container_width = dpg.get_item_width('log_region')
        wrap_width = max(container_width - 10, 0)

        # Render each buffered line as a wrapped group
        for line in self._buffer:
            # Start a horizontal group to keep segments together
            with dpg.group(parent='log_region', horizontal=True):
                rich_text = Text.from_ansi(line)
                plain = rich_text.plain
                spans = rich_text.spans
                last_idx = 0

                # Iterate all spans, outputting unstyled and styled segments
                for span in spans:
                    start, end, style = span.start, span.end, span.style
                    # Unstyled prefix
                    if start > last_idx:
                        seg = plain[last_idx:start]
                        dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width)
                    # Styled segment
                    seg = plain[start:end]
                    if style.color:
                        r, g, b = style.color.get_truecolor()
                    else:
                        r, g, b = 255, 255, 255
                    dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width, color=(r, g, b))
                    last_idx = end

                # Trailing text
                if last_idx < len(plain):
                    seg = plain[last_idx:]
                    dpg.add_text(seg, parent=dpg.last_container(), wrap=wrap_width)

        # Auto-scroll to bottom
        dpg.set_y_scroll('log_region', dpg.get_y_scroll_max('log_region'))
