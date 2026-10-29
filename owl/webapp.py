"""Minimal local OWL HTTP UI with same-origin task submission and no secrets editor."""

from __future__ import annotations

import json
import logging
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from owl.providers import PROVIDERS
from owl.runtime import run_task

_LOG = logging.getLogger(__name__)
_STATIC = Path(__file__).resolve().parent / "static"
_RUN_LIMIT = threading.BoundedSemaphore(1)
_MAX_REQUEST_BYTES = 32768
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}


class OwlHandler(BaseHTTPRequestHandler):
    """Localhost-only browser interface. Never logs prompt or model content."""

    def log_message(self, fmt, *args):
        _LOG.debug("HTTP request: %s %s", self.command, self.path)

    def _headers(self, content_type: str, size: int, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )
        self.end_headers()

    def _allowed_host(self) -> bool:
        host = self.headers.get("Host", "").lower()
        return host in {
            f"localhost:{self.server.server_port}",
            f"127.0.0.1:{self.server.server_port}",
            f"[::1]:{self.server.server_port}",
        }

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=True).encode("utf-8")
        self._headers("application/json; charset=utf-8", len(body), status)
        self.wfile.write(body)

    def do_GET(self):
        if not self._allowed_host():
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Host"})
        if self.path in _ASSETS:
            filename, content_type = _ASSETS[self.path]
            content = (_STATIC / filename).read_bytes()
            self._headers(content_type, len(content))
            self.wfile.write(content)
        elif self.path == "/health":
            self._json(200, {"status": "ok"})
        elif self.path == "/api/config":
            provider = os.environ.get("OWL_PROVIDER", "ollama")
            mode = os.environ.get("OWL_MODE", "assistant")
            self._json(200, {
                "provider": provider if provider in PROVIDERS else "ollama",
                "mode": mode if mode in ("assistant", "workforce") else "assistant",
            })
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        if not self._allowed_host():
            return self._json(400, {"error": "Invalid Host"})
        origin = self.headers.get("Origin", "")
        allowed_origins = {
            f"http://localhost:{self.server.server_port}",
            f"http://127.0.0.1:{self.server.server_port}",
            f"http://[::1]:{self.server.server_port}",
        }
        if origin not in allowed_origins:
            return self._json(403, {"error": "Cross-origin POST denied"})
        if self.path != "/api/run":
            return self._json(404, {"error": "Not found"})
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self._json(415, {"error": "Use application/json"})
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            return self._json(400, {"error": "Invalid Content-Length"})
        if length < 2 or length > _MAX_REQUEST_BYTES:
            return self._json(413, {"error": "Invalid request size"})
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            task, provider, model, mode = (
                data.get("task"), data.get("provider"), data.get("model"), data.get("mode")
            )
            if (not isinstance(task, str) or not isinstance(provider, str)
                    or not isinstance(model, str) or not isinstance(mode, str)):
                raise ValueError("Invalid task or provider parameters")
            if provider not in PROVIDERS or mode not in ("assistant", "workforce"):
                raise ValueError("Unsupported provider or mode")
            if len(model) > 200:
                raise ValueError("Invalid model identifier")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            return self._json(400, {"error": str(exc)})
        if not _RUN_LIMIT.acquire(blocking=False):
            return self._json(429, {"error": "A task is already running"})
        try:
            result = run_task(task, provider, model.strip() or None, mode)
            return self._json(200, {"answer": result})
        except ValueError as exc:
            return self._json(422, {"error": str(exc)})
        except Exception as exc:
            _LOG.error("Model invocation failed: %s", type(exc).__name__)
            return self._json(502, {"error": "Model invocation failed; verify endpoint and logs"})
        finally:
            _RUN_LIMIT.release()


def make_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    bind = host or os.getenv("OWL_SERVER_HOST", "127.0.0.1")
    address_port = port if port is not None else int(os.getenv("OWL_SERVER_PORT", "7860"))
    if bind not in ("localhost", "127.0.0.1", "::1"):
        if os.getenv("OWL_ALLOW_NON_LOOPBACK") != "I_UNDERSTAND_THE_RISK":
            raise ValueError("Non-loopback bind requires OWL_ALLOW_NON_LOOPBACK=I_UNDERSTAND_THE_RISK")
    return ThreadingHTTPServer((bind, address_port), OwlHandler)


def main() -> None:
    logging.basicConfig(level=os.getenv("OWL_LOG_LEVEL", "WARNING"))
    server = make_server()
    try:
        _LOG.warning("OWL local UI bound to %s:%d", *server.server_address[:2])
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
