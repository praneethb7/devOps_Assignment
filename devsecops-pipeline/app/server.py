"""Small HTTP surface for the booking service."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from app.bookings import BookingError, sign_reference, validate_reference

VERSION = os.getenv("APP_VERSION", "dev")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)

        if url.path == "/health":
            return self._send(200, {"status": "ok", "version": VERSION})

        if url.path == "/ready":
            try:
                sign_reference("YT-ABC123")
            except BookingError as exc:
                return self._send(503, {"status": "not ready", "reason": str(exc)})
            return self._send(200, {"status": "ready"})

        if url.path == "/sign":
            ref = parse_qs(url.query).get("ref", [""])[0]
            try:
                return self._send(200, {"reference": validate_reference(ref),
                                        "signature": sign_reference(ref)})
            except BookingError as exc:
                return self._send(400, {"error": str(exc)})

        self._send(404, {"error": "not found"})

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), Handler).serve_forever()


if __name__ == "__main__":
    main()
