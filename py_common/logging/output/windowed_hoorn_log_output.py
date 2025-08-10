import threading
import queue

from flask import Flask, render_template_string
from flask_socketio import SocketIO

from rich.text import Text

from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface

# HTML template for the web UI, with only a single inner scrollbar
default_INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Hoorn Log</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
      background: #1e1e1e;
      color: #ffffff;
      font-family: monospace;
    }
    #log {
      white-space: pre-wrap;
      padding: 1em;
      height: 100%;
      overflow-y: auto;
      box-sizing: border-box;
    }
  </style>
  <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
  <div id="log"></div>
  <script>
    const socket = io();
    const container = document.getElementById('log');
    const MAX_LINES = 1000; // Set the maximum number of lines to keep

    socket.on('log_line', ({ line }) => {
      const span = document.createElement('span');
      span.innerHTML = line;
      container.appendChild(span);
      container.appendChild(document.createElement('br'));

      // If we have too many lines, remove the oldest ones
      while (container.children.length > MAX_LINES * 2) {
        container.removeChild(container.firstChild);
        container.removeChild(container.firstChild);
      }

      // Always scroll the new log entry into view
      span.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  </script>
</body>
</html>
'''

def _run_ui(queue_obj):
    """
    Starts Flask-SocketIO server in its own thread.
    """
    print(f"Starting Hoorn Log UI on http://127.0.0.1:5000 (threaded)")
    app, socketio, stop_event = _create_app(queue_obj)
    # Listen on all interfaces so host/VM port forwards work naturally
    socketio.run(app, host='0.0.0.0', port=5000)
    stop_event.set()


def _create_app(queue_obj):
    """
    Builds the Flask app, configures SocketIO, and starts the polling background task.
    """
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')
    stop_event = threading.Event()

    @app.route('/')
    def index():
        return render_template_string(default_INDEX_HTML)

    def poll_and_emit():
        while not stop_event.is_set():
            try:
                while True:
                    line = queue_obj.get_nowait()
                    socketio.emit('log_line', {'line': _convert_to_html(line)})
            except queue.Empty:
                pass
            socketio.sleep(0)

    # Launch polling as a SocketIO background task
    socketio.start_background_task(poll_and_emit)
    return app, socketio, stop_event


class WindowedHoornLogOutput(HoornLogOutputInterface):
    """
    Browser-based real-time log viewer using Flask + SocketIO.
    """
    def __init__(
            self,
            max_separator_length: int = 30
    ):
        super().__init__(is_child=True)
        self._sep_len = max_separator_length
        self._queue = queue.Queue()
        self._start_server_thread()

    def output(self, hoorn_log: HoornLog, encoding: str = "utf-8") -> None:
        """
        Enqueue a formatted line for the UI; dropped if marked default-ignore.
        """
        msg = hoorn_log.formatted_message
        if "${ignore=default}" in msg:
            return
        prefix = f"[{hoorn_log.separator:<{self._sep_len}}]"
        self._queue.put(f"{prefix} {msg}")

    def save(self) -> None:
        """
        No explicit shutdown; server thread runs until process exit.
        """
        pass

    def _start_server_thread(self) -> None:
        """
        Spins up the Flask-SocketIO UI in a background thread.
        """
        thread = threading.Thread(
            target=_run_ui,
            args=[self._queue],
            daemon=True
        )
        thread.start()


def _convert_to_html(line: str) -> str:
    """
    Turn an ANSI-colored log line into HTML <span> with inline CSS.
    """
    rt = Text.from_ansi(line)
    plain, spans = rt.plain, rt.spans
    last = 0
    out = []
    for sp in spans:
        if sp.start > last:
            out.append(_wrap_color(plain[last:sp.start], '#ffffff'))
        segment = plain[sp.start:sp.end]
        color = sp.style.color.get_truecolor() if sp.style.color else (255,255,255)
        hexc = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        out.append(_wrap_color(segment, hexc))
        last = sp.end
    if last < len(plain):
        out.append(_wrap_color(plain[last:], '#ffffff'))
    return ''.join(out)


def _wrap_color(text: str, color: str) -> str:
    return f"<span style='color:{color}'>{text}</span>"
