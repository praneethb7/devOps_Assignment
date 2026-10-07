"""A tiny service that exposes Prometheus metrics for the yatri booking flow.

Standard library only - the /metrics text format is simple enough to emit
directly, and that makes the exposition format visible rather than hidden
behind a client library.
"""
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

START = time.time()

# counters only ever go up; gauges go up and down; histograms bucket observations
bookings_total = {"confirmed": 0, "failed": 0}
inflight = 0
latency_buckets = {0.05: 0, 0.1: 0, 0.25: 0, 0.5: 0, 1.0: 0, float("inf"): 0}
latency_sum = 0.0
latency_count = 0
lock = threading.Lock()


def observe(seconds: float, outcome: str) -> None:
    global latency_sum, latency_count
    with lock:
        bookings_total[outcome] += 1
        latency_sum += seconds
        latency_count += 1
        # Increment only the FIRST bucket the observation falls into; the
        # /metrics handler turns these into the cumulative counts the
        # Prometheus histogram format requires. Incrementing every bucket
        # here as well double-counts, and the giveaway is that the +Inf
        # bucket stops matching _count.
        for upper in sorted(latency_buckets):
            if seconds <= upper:
                latency_buckets[upper] += 1
                break


def traffic() -> None:
    """Generate booking activity so the dashboards have something to show."""
    global inflight
    while True:
        with lock:
            inflight += 1
        took = random.expovariate(1 / 0.12)
        time.sleep(min(took, 1.5))
        observe(took, "failed" if random.random() < 0.08 else "confirmed")
        with lock:
            inflight -= 1
        time.sleep(random.uniform(0.05, 0.4))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        with lock:
            lines = [
                "# HELP yatri_bookings_total Bookings processed, by outcome.",
                "# TYPE yatri_bookings_total counter",
                f'yatri_bookings_total{{outcome="confirmed"}} {bookings_total["confirmed"]}',
                f'yatri_bookings_total{{outcome="failed"}} {bookings_total["failed"]}',
                "# HELP yatri_bookings_inflight Bookings currently being processed.",
                "# TYPE yatri_bookings_inflight gauge",
                f"yatri_bookings_inflight {inflight}",
                "# HELP yatri_booking_duration_seconds Booking latency.",
                "# TYPE yatri_booking_duration_seconds histogram",
            ]
            cumulative = 0
            for upper in sorted(latency_buckets):
                cumulative += latency_buckets[upper]
                label = "+Inf" if upper == float("inf") else upper
                lines.append(
                    f'yatri_booking_duration_seconds_bucket{{le="{label}"}} {cumulative}'
                )
            lines += [
                f"yatri_booking_duration_seconds_sum {latency_sum:.4f}",
                f"yatri_booking_duration_seconds_count {latency_count}",
                "# HELP yatri_uptime_seconds Seconds since process start.",
                "# TYPE yatri_uptime_seconds gauge",
                f"yatri_uptime_seconds {time.time() - START:.1f}",
            ]

        body = ("\n".join(lines) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    for _ in range(4):
        threading.Thread(target=traffic, daemon=True).start()
    port = int(os.getenv("PORT", "8000"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
