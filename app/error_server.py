"""Simple Flask server to receive client-side error logs and print them.

This exposes a single ``/client-error`` endpoint that accepts JSON payloads
containing ``message`` and optional ``stack`` fields.  Incoming logs are
printed to stdout so that they are visible in Railway's log interface.
"""

from __future__ import annotations

import os
from flask import Flask, request

app = Flask(__name__)


@app.post("/client-error")
def client_error():
    """Receive a JSON payload describing a browser error and log it."""
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "<no message>")
    stack = data.get("stack", "")
    print(f"📣 ClientError: {message}\n{stack}")
    return {"status": "ok"}


def run_server() -> None:
    """Run the Flask app on the configured port."""
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

