"""
Sovereign Computer — Webhook Server
Exposes a local HTTP endpoint so SureThing (or any external caller) can
invoke the orchestrator remotely.

Usage:
    python webhook_server.py          # default port 9000
    PORT=8888 python webhook_server.py

POST /run
    Body: {"goal": "your goal here", "secret": "WEBHOOK_SECRET"}
    Returns: {"status": "ok", "artifacts": [...], "reflection": "..."}

GET /status
    Returns: {"status": "idle"} or {"status": "running", "goal": "..."}
"""

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Lazy import to avoid loading LangGraph before env is ready
def get_app():
    from sovereign_computer import app
    return app

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PORT           = int(os.getenv("PORT", 9000))
OUTPUT_DIR     = Path(os.getenv("OUTPUT_DIR", "./output"))

_state_lock = threading.Lock()
_current    = {"status": "idle", "goal": None}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quieter logs — only errors
        if "200" not in (args[1] if len(args) > 1 else ""):
            super().log_message(format, *args)

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            with _state_lock:
                self._send_json(200, dict(_current))
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/run":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        # Auth check
        if WEBHOOK_SECRET and data.get("secret") != WEBHOOK_SECRET:
            self._send_json(401, {"error": "unauthorized"})
            return

        goal = (data.get("goal") or "").strip()
        if not goal:
            self._send_json(400, {"error": "goal is required"})
            return

        with _state_lock:
            if _current["status"] == "running":
                self._send_json(409, {"error": "already running", "goal": _current["goal"]})
                return
            _current["status"] = "running"
            _current["goal"]   = goal

        try:
            orchestrator = get_app()
            result = orchestrator.invoke({
                "goal": goal,
                "tasks": [],
                "results": {},
                "artifacts": [],
                "reflection": "",
            })
            # Read output file if it exists
            out_file = OUTPUT_DIR / "results.md"
            output_text = out_file.read_text() if out_file.exists() else ""

            with _state_lock:
                _current["status"] = "idle"
                _current["goal"]   = None

            self._send_json(200, {
                "status":     "ok",
                "goal":       goal,
                "artifacts":  result.get("artifacts", []),
                "reflection": result.get("reflection", ""),
                "output":     output_text,
            })
        except Exception as e:
            with _state_lock:
                _current["status"] = "idle"
                _current["goal"]   = None
            self._send_json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"\n🌐 Sovereign Computer Webhook Server")
    print(f"   Listening on http://0.0.0.0:{PORT}")
    print(f"   POST /run  — trigger orchestrator")
    print(f"   GET  /status — check state")
    if WEBHOOK_SECRET:
        print(f"   Auth: secret required ✓")
    else:
        print(f"   ⚠  No WEBHOOK_SECRET set — set one in .env for security")
    print()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
