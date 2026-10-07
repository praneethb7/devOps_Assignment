import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest

from app.main import Handler


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def get(url):
    with urllib.request.urlopen(url) as response:
        return response.status, json.loads(response.read())


def test_health_returns_ok(server):
    status, body = get(f"{server}/health")
    assert status == 200
    assert body["status"] == "ok"


def test_fare_endpoint_returns_a_total(server):
    status, body = get(f"{server}/fare?km=100&passengers=2&class=premium")
    assert status == 200
    assert body == {"total": 880.0, "currency": "INR"}


def test_bad_input_returns_400(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(f"{server}/fare?km=-5")
    assert exc.value.code == 400
