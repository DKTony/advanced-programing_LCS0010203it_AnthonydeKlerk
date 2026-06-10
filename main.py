from __future__ import annotations

import threading
import time

from api import create_app, start_manifest_worker
from gui import launch_gui


def main() -> None:
    host = "127.0.0.1"
    port = 5000
    app = create_app()
    repository = app.extensions["repository"]

    flask_thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        name="flask-api",
        daemon=True,
    )
    flask_thread.start()
    print(f"[main] started Flask API thread at http://{host}:{port}", flush=True)
    start_manifest_worker(repository)

    time.sleep(0.75)
    print("[main] launching Tkinter GUI", flush=True)
    launch_gui(f"http://{host}:{port}/api")


if __name__ == "__main__":
    main()
