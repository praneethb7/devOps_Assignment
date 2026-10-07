"""Minimal HTTP API over the fare rules, using only the standard library.

No framework on purpose: the point of this session is the pipeline, and a
dependency-free app keeps the CI job about build and test rather than about
resolving a lockfile.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from app.fares import FareError, total

VERSION = os.getenv("APP_VERSION", "dev")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)

        if url.path == "/health":
            return self._send(200, {"status": "ok", "version": VERSION})

        if url.path == "/fare":
            q = parse_qs(url.query)
            try:
                amount = total(
                    distance_km=float(q.get("km", ["0"])[0]),
                    passengers=int(q.get("passengers", ["1"])[0]),
                    travel_class=q.get("class", ["economy"])[0],
                    peak=q.get("peak", ["false"])[0].lower() == "true",
                )
            except (FareError, ValueError) as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(200, {"total": amount, "currency": "INR"})

        self._send(404, {"error": "not found"})

    def log_message(self, *args) -> None:        # keep CI logs readable
        pass


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
